"""
Factory Endpoints - Curation Pipeline (SYN-86)
===============================================

Endpoints para a Vitrine de Curadoria Tinder-Style.
Consome a tabela `pending_approvals` e orquestra:
  - Listagem de vídeos pendentes
  - Aprovação (injeta no scheduler via batch_manager/smart_logic)
  - Rejeição (remove do DB + garbage collection do arquivo)
  - Inversão (FFmpeg vstack reverso: gameplay no topo, facecam embaixo)
"""

import os
import json
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import PendingApproval, Profile, Army, army_profiles

logger = logging.getLogger("FactoryAPI")

router = APIRouter()


# ─── Response Models ────────────────────────────────────────────────────

class ClipDetail(BaseModel):
    index: int
    title: Optional[str] = None
    duration: Optional[float] = None
    views: Optional[int] = None
    creator: Optional[str] = None
    broadcaster: Optional[str] = None
    game: Optional[str] = None

class PendingItemResponse(BaseModel):
    id: int
    clip_job_id: Optional[int] = None
    video_path: str
    thumbnail_path: Optional[str] = None
    streamer_name: Optional[str] = None
    title: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    caption_generated: bool = False
    transcript: Optional[str] = None  # Whisper transcript for AI generation
    status: str
    created_at: datetime
    target_army_id: Optional[int] = None
    target_name: Optional[str] = None
    available_profiles: Optional[List[dict]] = None
    clips: Optional[List[ClipDetail]] = None  # Individual clip metadata for reordering


# ─── Helpers ─────────────────────────────────────────────────────────────

def _resolve_profiles_for_approval(item: PendingApproval, db: Session, profile_slug: Optional[str] = None) -> List["Profile"]:
    """
    Resolve quais Profiles usar para agendar o video aprovado.

    Prioridade:
    1. Profiles vinculados ao Army do TwitchTarget do job
    2. profile_slug explicito (frontend escolheu)
    3. Primeiro Profile ativo como fallback
    """
    # 1. Via cadeia: ClipJob → TwitchTarget → army_id → Army.profiles
    if item.clip_job_id:
        from core.clipper.models import ClipJob, TwitchTarget
        job = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first()
        if job and job.target_id:
            target = db.query(TwitchTarget).filter(TwitchTarget.id == job.target_id).first()
            if target and target.army_id:
                army = db.query(Army).filter(Army.id == target.army_id).first()
                if army and army.profiles:
                    # Pegar TODOS os profiles ativos do army
                    active_profiles = [p for p in army.profiles if p.active]
                    if active_profiles:
                        return active_profiles

    # 2. Slug explicito
    if profile_slug:
        profile = db.query(Profile).filter(Profile.slug == profile_slug, Profile.active == True).first()
        if profile:
            return [profile]
        return []

    # 3. Fallback: primeiro profile ativo
    profile = db.query(Profile).filter(Profile.active == True).first()
    return [profile] if profile else []


def _get_available_profiles_for_item(item: PendingApproval, db: Session) -> List[dict]:
    """Retorna profiles disponiveis para o frontend exibir na selecao."""
    profiles = db.query(Profile).filter(Profile.active == True).all()
    result = []
    for p in profiles:
        result.append({
            "slug": p.slug,
            "username": p.username,
            "label": p.label,
            "avatar_url": p.avatar_url,
        })
    return result


# ─── GET /pending ────────────────────────────────────────────────────────

@router.get("/pending", response_model=List[PendingItemResponse])
def list_pending(db: Session = Depends(get_db)):
    """
    Lista todos os vídeos pendentes de curadoria.
    Ordenados do mais recente para o mais antigo.
    Inclui army_id e profiles disponiveis para selecao no frontend.
    """
    items = (
        db.query(PendingApproval)
        .filter(PendingApproval.status == "pending")
        .order_by(PendingApproval.created_at.desc())
        .limit(50)
        .all()
    )

    available_profiles = _get_available_profiles_for_item(None, db) if items else []

    results = []
    for item in items:
        # Resolver army_id e target_name via ClipJob → TwitchTarget
        target_army_id = None
        target_name = None
        if item.clip_job_id:
            from core.clipper.models import ClipJob, TwitchTarget
            job = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first()
            if job and job.target_id:
                target = db.query(TwitchTarget).filter(TwitchTarget.id == job.target_id).first()
                if target:
                    target_army_id = target.army_id
                    target_name = target.channel_name

        # Extrair transcript do ClipJob.whisper_result para uso na geração de caption
        transcript_text = None
        if item.clip_job_id:
            job_for_transcript = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first() if not job else job
            if job_for_transcript and job_for_transcript.whisper_result:
                # whisper_result é uma lista de dicts, cada um com "text"
                transcript_parts = [
                    t.get("text", "") for t in (job_for_transcript.whisper_result or []) if t.get("text")
                ]
                transcript_text = " ".join(transcript_parts) if transcript_parts else None

        # Extrair detalhes individuais dos clips para reordering UI
        clips_detail = None
        if item.clip_job_id and job:
            metadata_list = job.clip_metadata or []
            clip_count = len(job.clip_urls) if job.clip_urls else 0
            if clip_count > 0:
                clips_detail = []
                for i in range(clip_count):
                    meta = metadata_list[i] if i < len(metadata_list) else {}
                    clips_detail.append(ClipDetail(
                        index=i,
                        title=meta.get("title"),
                        duration=meta.get("duration"),
                        views=meta.get("views") or meta.get("view_count"),
                        creator=meta.get("creator") or meta.get("creator_name"),
                        broadcaster=meta.get("broadcaster_name"),
                        game=meta.get("game") or meta.get("game_name"),
                    ))

        results.append(PendingItemResponse(
            id=item.id,
            clip_job_id=item.clip_job_id,
            video_path=item.video_path,
            thumbnail_path=item.thumbnail_path,
            streamer_name=item.streamer_name,
            title=item.title,
            duration_seconds=item.duration_seconds,
            file_size_bytes=item.file_size_bytes,
            caption=item.caption,
            hashtags=item.hashtags or [],
            caption_generated=item.caption_generated or False,
            transcript=transcript_text,
            status=item.status,
            created_at=item.created_at,
            target_army_id=target_army_id,
            target_name=target_name,
            available_profiles=available_profiles,
            clips=clips_detail,
        ))
    return results


# ─── POST /approve/{id} — SYN-78: Smart Queue Pipeline ──────────────────

class ApproveRequest(BaseModel):
    profile_slug: Optional[str] = None
    schedule_mode: str = "smart"  # "smart" | "specific" | "now"
    schedule_date: Optional[str] = None  # "2026-03-15" (ISO date)
    schedule_time: Optional[str] = None  # "14:30" (HH:MM)
    schedule_hours: Optional[List[int]] = None  # [12, 18] override for smart mode


@router.post("/approve/{item_id}")
async def approve_item(
    item_id: int,
    body: ApproveRequest = ApproveRequest(),
    db: Session = Depends(get_db),
):
    """
    Aprova um vídeo pendente e o injeta na Smart Queue.

    Modos de agendamento:
    - "smart": Smart Queue distribui automaticamente nos horários configurados
    - "specific": Agendar para data/hora exata (para testes ou datas estratégicas)
    - "now": Agendar para o próximo slot disponível (dentro de 1h)

    Resolucao de perfil (prioridade):
    1. profile_slug passado no body (frontend escolheu)
    2. Profile vinculado ao Army do TwitchTarget do job
    3. Primeiro Profile ativo como fallback
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    if item.status != "pending":
        raise HTTPException(status_code=400, detail=f"Item já processado: {item.status}")

    # Verificar arquivo existe
    if not os.path.exists(item.video_path):
        raise HTTPException(status_code=400, detail=f"Arquivo não encontrado: {item.video_path}")

    try:
        from core.auto_scheduler import create_queue, schedule_next_batch
        from zoneinfo import ZoneInfo

        SP_TZ = ZoneInfo("America/Sao_Paulo")

        # Resolver profiles inteligentemente
        profiles = _resolve_profiles_for_approval(item, db, body.profile_slug)
        if not profiles:
            raise HTTPException(status_code=400, detail="Nenhum perfil ativo encontrado para agendamento")

        # Horários padrão de publicação
        schedule_hours = body.schedule_hours or [12, 18]

        # Montar caption final (sem hashtags — o uploader insere as hashtags)
        final_caption = item.caption or item.title or ""
        final_hashtags = item.hashtags or []

        from core.models import ScheduleItem

        results = []
        overall_scheduled_time = None

        for p in profiles:
            # 1. Inserir na Smart Queue
            queue_items = create_queue(
                profile_slug=p.slug,
                videos=[{
                    "path": item.video_path,
                    "caption": final_caption,
                    "hashtags": final_hashtags,
                    "privacy_level": "public_to_everyone",
                }],
                posts_per_day=len(schedule_hours),
                schedule_hours=schedule_hours,
                db=db,
            )

            p_scheduled_time = None
            result = None

            if body.schedule_mode == "specific" and body.schedule_date and body.schedule_time:
                # Modo específico: agendar para data/hora exata
                hour, minute = map(int, str(body.schedule_time).split(":"))
                target_dt = datetime.fromisoformat(str(body.schedule_date)).replace(
                    hour=hour, minute=minute, second=0
                )
                # Criar ScheduleItem diretamente com o horário escolhido
                sched_item = ScheduleItem(
                    profile_slug=p.slug,
                    video_path=item.video_path,
                    scheduled_time=target_dt,
                    status="pending",
                    metadata_info={
                        "caption": final_caption,
                        "hashtags": final_hashtags,
                        "privacy_level": "public_to_everyone",
                        "source": "approve_specific",
                    }
                )
                db.add(sched_item)
                db.flush()
                if queue_items:
                    queue_items[0].scheduled_at = target_dt
                    queue_items[0].status = "scheduled"
                    queue_items[0].schedule_item_id = sched_item.id
                db.commit()
                p_scheduled_time = target_dt.isoformat()
                result = {"scheduled": 1, "failed": 0, "queued_remaining": 0}

            elif body.schedule_mode == "now":
                # Modo imediato: próximo slot em 1 minuto (scheduler polls a cada 30s)
                now = datetime.now(SP_TZ)
                target_dt = (now + timedelta(minutes=1)).replace(tzinfo=None)
                # Criar ScheduleItem para execução em ~1 minuto
                sched_item = ScheduleItem(
                    profile_slug=p.slug,
                    video_path=item.video_path,
                    scheduled_time=target_dt,
                    status="pending",
                    metadata_info={
                        "caption": final_caption,
                        "hashtags": final_hashtags,
                        "privacy_level": "public_to_everyone",
                        "source": "approve_now",
                    }
                )
                db.add(sched_item)
                db.flush()
                if queue_items:
                    queue_items[0].scheduled_at = target_dt
                    queue_items[0].status = "scheduled"
                    queue_items[0].schedule_item_id = sched_item.id
                db.commit()
                p_scheduled_time = target_dt.isoformat()
                result = {"scheduled": 1, "failed": 0, "queued_remaining": 0}

            else:
                # Modo smart (padrão): distribuição automática via calculate_next_slots
                result = await schedule_next_batch(
                    profile_slug=p.slug,
                    batch_size=1,
                    db=db,
                )

            if not p_scheduled_time and queue_items and hasattr(queue_items[0], 'scheduled_at') and queue_items[0].scheduled_at:
                p_scheduled_time = queue_items[0].scheduled_at.isoformat()
            
            if not overall_scheduled_time:
                overall_scheduled_time = p_scheduled_time

            logger.info(f"Item #{item_id} aprovado [{body.schedule_mode}] -> perfil @{p.slug} | resultado: {result}")
            results.append({"profile": p.slug, "result": result})

        # 3. Marcar como aprovado
        item.status = "approved"
        db.commit()

        return {
            "message": f"Vídeo aprovado e inserido na Smart Queue para {len(profiles)} perfil(s)",
            "profile": profiles[0].slug,
            "profiles": [p.slug for p in profiles],
            "schedule_mode": body.schedule_mode,
            "scheduled_time": overall_scheduled_time,
            "queue_result": results[0]["result"] if results else None,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao aprovar item #{item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /queue-status — SYN-78: Status da Smart Queue ──────────────────

@router.get("/queue-status")
def get_queue_status(db: Session = Depends(get_db)):
    """
    Retorna o status da Smart Queue para o frontend (widget de contadores).
    """
    from core.models import VideoQueue, Profile

    profile = db.query(Profile).filter(Profile.active == True).first()
    if not profile:
        return {"queued": 0, "scheduled": 0, "failed": 0, "total_pending": 0}

    queued = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile.slug,
        VideoQueue.status == "queued"
    ).count()

    scheduled = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile.slug,
        VideoQueue.status == "scheduled"
    ).count()

    failed = db.query(VideoQueue).filter(
        VideoQueue.profile_slug == profile.slug,
        VideoQueue.status == "failed"
    ).count()

    total_pending = db.query(PendingApproval).filter(
        PendingApproval.status == "pending"
    ).count()

    return {
        "profile": profile.slug,
        "queued": queued,
        "scheduled": scheduled,
        "failed": failed,
        "total_pending": total_pending,
    }


# ─── PATCH /caption/{id} — Salvar caption editada manualmente ────────────

class CaptionUpdate(BaseModel):
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None

@router.patch("/caption/{item_id}")
def update_caption(item_id: int, payload: CaptionUpdate, db: Session = Depends(get_db)):
    """Salva a caption/hashtags editadas pelo usuario no card de curadoria."""
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    if payload.caption is not None:
        item.caption = payload.caption
    if payload.hashtags is not None:
        item.hashtags = payload.hashtags
    db.commit()
    return {"message": "Caption atualizada", "id": item_id}


# ─── POST /generate-caption/{id} — Gerar caption via Oracle (Groq) ──────

class GenerateCaptionOptions(BaseModel):
    tone: str = "Viral"
    length: str = "short"
    include_hashtags: bool = True
    instruction: str = ""

@router.post("/generate-caption/{item_id}")
async def generate_caption_for_item(item_id: int, options: GenerateCaptionOptions, db: Session = Depends(get_db)):
    """
    Gera caption + hashtags via Oracle/Groq para um PendingApproval.
    Coleta contexto completo: transcript Whisper, metadados dos clips (game, títulos,
    views, broadcaster), nome do streamer, duração do vídeo final.
    Usa Personas UX Writer especializadas por tom.
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    # ── Extrair contexto completo do ClipJob ──
    transcript_text = ""
    streamer = item.streamer_name or ""
    game_name = ""
    clip_titles = []
    clip_views = []
    broadcasters = set()
    total_clips = 0
    target_type = ""

    if item.clip_job_id:
        from core.clipper.models import ClipJob, TwitchTarget
        job = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first()
        if job:
            # Transcript
            if job.whisper_result:
                parts = [t.get("text", "") for t in (job.whisper_result or []) if t.get("text")]
                transcript_text = " ".join(parts)

            # Metadados dos clips (game, titles, views, broadcasters)
            if job.clip_metadata:
                total_clips = len(job.clip_metadata)
                for meta in job.clip_metadata:
                    if meta.get("game"):
                        game_name = meta["game"]
                    if meta.get("title"):
                        clip_titles.append(meta["title"])
                    if meta.get("view_count"):
                        clip_views.append(meta["view_count"])
                    if meta.get("broadcaster_name"):
                        broadcasters.add(meta["broadcaster_name"])

            # Target info (tipo: canal ou categoria)
            if job.target_id:
                target = db.query(TwitchTarget).filter(TwitchTarget.id == job.target_id).first()
                if target:
                    target_type = target.target_type or "channel"
                    if not streamer:
                        # Para targets de categoria, usar o broadcaster real dos metadados
                        if target_type == "category" and broadcasters:
                            streamer = next(iter(broadcasters))
                        elif target.channel_name:
                            streamer = target.channel_name

    # ── Detectar categoria para hashtags dinâmicas ──
    NON_GAMING_CATEGORIES = {
        "just chatting", "irl", "talk shows & podcasts", "asmr",
        "music", "art", "beauty & body art", "food & drink",
        "sports", "travel & outdoors", "fitness & health",
        "pools, hot tubs, and beaches", "makers & crafting",
        "special events", "politics", "science & technology",
    }
    is_gaming = True  # default
    category_lower = game_name.lower().strip() if game_name else ""
    if category_lower in NON_GAMING_CATEGORIES or not game_name:
        is_gaming = False

    # Hashtag guidance dinâmica baseada na categoria real
    if is_gaming:
        hashtag_guidance_viral = f"3-5 tags. Misture alcance (#fyp) com nicho do jogo (#{category_lower.replace(' ', '').replace(':', '')}). NÃO use tags genéricas de categorias que não sejam do vídeo."
        hashtag_guidance_polemico = f"3-5 tags. Mix do jogo e da comunidade gamer. Use o nome real do jogo como tag."
        hashtag_guidance_engracado = f"3-5 tags. Tom leve (#humor) + jogo específico (#{category_lower.replace(' ', '').replace(':', '')}). NÃO coloque #gaming se o foco é humor."
        hashtag_guidance_pro = f"3-5 tags. Tom editorial (#twitch #gameplay) + nome completo do jogo."
    else:
        # IRL / Just Chatting / Non-gaming
        hashtag_guidance_viral = f"3-5 tags. Misture alcance (#fyp) com nicho da categoria (#{category_lower.replace(' ', '').replace(':', '') or 'twitch'}). NUNCA use #gaming se o conteúdo não é sobre jogos."
        hashtag_guidance_polemico = f"3-5 tags. Focadas na comunidade e no tipo de conteúdo. NUNCA use #gaming."
        hashtag_guidance_engracado = f"3-5 tags. Tom leve (#humor #react) + tags do nicho. NUNCA use #gaming."
        hashtag_guidance_pro = f"3-5 tags. Tom editorial (#twitch #livestream) + contexto do conteúdo. NUNCA use #gaming se não é sobre jogos."

    # ── Anti-repetição: seed aleatório para variar o output ──
    creativity_seed = random.randint(1000, 9999)
    creativity_angles = [
        "Foque na REAÇÃO mais intensa do clipe.",
        "Destaque o MOMENTO mais inesperado.",
        "Construa a caption como se fosse uma NARRAÇÃO cinematográfica.",
        "Escreva como se estivesse contando pra um amigo que não assistiu.",
        "Foque no CONTRASTE entre o que o streamer esperava e o que aconteceu.",
        "Comece pelo RESULTADO e deixe o contexto pra curiosidade.",
        "Use a fala mais marcante do streamer como base.",
        "Escreva como legenda de meme — curta e com impacto.",
    ]
    chosen_angle = random.choice(creativity_angles)

    # ── Personas UX Writer por Tom ──
    PERSONAS = {
        "Viral": f"""Você escreve como um brasileiro de 20 e poucos anos que vive no TikTok.
Você NÃO é um copywriter — você é alguém que faz o celular tremer de notificação.

COMO VOCÊ PENSA:
Você vê o clipe e pensa "mano, o que eu diria pros meus amigos sobre isso?". A caption é essa reação natural, só que escrita pra viralizar. Você não "cria conteúdo", você REAGE — e as pessoas se identificam com a sua reação.

SEU TOM:
- Escreve como fala: sem filtro, direto, como se tivesse mandando áudio no grupo
- Caps lock é grito — use quando o momento pede grito de verdade
- Emoji só quando potencializa (💀 = morri de rir, não decoração)
- Nunca mais de 2-3 linhas. Se precisa de mais, o clipe que fale
- Gírias SÓ as que você usaria de verdade: "simplesmente", "mano", "na moral", "o bixo"
- NUNCA comece a caption com a mesma frase/estrutura de outras captions. Cada uma deve ser ÚNICA.

EXEMPLOS DE ESTRUTURA (varie entre eles, NUNCA repita a mesma abertura):
- "ele simplesmente DESISTIU no meio do boss kkkk"
- "a cara dele quando percebeu o que fez 💀"
- "ninguém tava preparado pra esse momento"
- "mano eu to passando mal com essa reação"

HASHTAGS: {hashtag_guidance_viral}

[SEED DE CRIATIVIDADE: {creativity_seed}] — Use esse número como inspiração subconsciente para gerar algo ÚNICO.
[ÂNGULO: {chosen_angle}]""",

        "Polêmico": f"""Você é aquele amigo que assiste o clipe e solta uma opinião que faz todo mundo querer responder.
Você NÃO é tóxico — você é ASSERTIVO. Fala o que pensa com peito e confiança.

COMO VOCÊ PENSA:
Você viu algo no clipe que merece ser dito em voz alta. Pode ser elogio forte, crítica certeira, ou uma verdade que ninguém quer admitir. O ponto é: quem lê vai querer concordar OU discordar — e vai comentar de qualquer jeito.

SEU TOM:
- Direto como conversa de bar. Sem rodeios, sem "na minha humilde opinião"
- Perguntas retóricas que cutucam
- Tome partido. Se o cara mandou bem, FALA. Se errou feio, FALA
- A provocação vem de confiança, não de grosseria
- NUNCA use "hot take:", "opinião impopular:" ou qualquer prefixo artificial
- NUNCA comece igual a captions anteriores. Cada uma é ÚNICA.

EXEMPLOS DE ESTRUTURA (varie, NUNCA repita):
- "esse cara é o MELHOR e vocês não tão prontos pra essa conversa"
- "se você morreu nessa parte, nem adianta continuar"
- "vocês tão dormindo nesse streamer e vai se arrepender"
- "fala que eu to errado nos comentários. vai."

HASHTAGS: {hashtag_guidance_polemico}

[SEED DE CRIATIVIDADE: {creativity_seed}]
[ÂNGULO: {chosen_angle}]""",

        "Engraçado": f"""Você é o amigo engraçado do grupo — aquele que narra o que tá acontecendo de um jeito que faz todo mundo rir.
Seu humor é natural, nunca forçado. Você não conta piada, você DESCREVE a realidade de um jeito absurdo.

COMO VOCÊ PENSA:
Você vê o clipe e sua cabeça já monta a narração cômica. O streamer fez merda? "o bixo literalmente escolheu a pior opção possível e ainda comemorou". A graça vem da observação, não da tentativa de ser engraçado.

SEU TOM:
- Humor de observação: descreva o que aconteceu, mas do ângulo mais ridículo
- Narração em terceira pessoa funciona demais: "ele realmente achou que ia dar certo"
- Auto-depreciação do viewer: a gente RI porque se identifica
- "kkkkk" e "KKKK" são pontuação — use onde o riso aconteceria naturalmente
- Setup curto → quebra de expectativa. Sem enrolação
- Referência a meme SÓ se encaixar organicamente, nunca force
- NUNCA comece igual a captions anteriores. Cada uma é ÚNICA.

EXEMPLOS DE ESTRUTURA (varie, NUNCA repita):
- "o bixo olhou pro zumbi e escolheu a opção 'correr gritando' kkkkkk"
- "tutorial de como NÃO jogar isso em 30 segundos"
- "streamer: 'tá tranquilo' / narrador: não estava tranquilo"
- "a confiança dele antes vs a realidade 2 segundos depois"

HASHTAGS: {hashtag_guidance_engracado}

[SEED DE CRIATIVIDADE: {creativity_seed}]
[ÂNGULO: {chosen_angle}]""",

        "Profissional": f"""Você é alguém que entende de conteúdo — e escreve como quem CUIDA do que publica.
Não é robótico, não é genérico. É alguém que viu o clipe, entendeu o que faz ele especial, e sabe apresentar isso com clareza.

COMO VOCÊ PENSA:
Você assiste o clipe pensando "por que isso merece atenção?". Pode ser uma jogada absurda, uma reação genuína, um momento raro. Você contextualiza sem explicar demais — quem entende vai valorizar, quem não entende vai ficar curioso.

SEU TOM:
- Linguagem limpa e confiante, sem gíria pesada mas sem parecer robô
- Dê contexto quando agrega: nome do streamer, o que tava acontecendo
- A caption deve funcionar sozinha, sem precisar do vídeo pra fazer sentido
- Sem emoji, sem caps lock. A força vem das palavras, não da formatação
- Pode ter um toque de admiração genuína quando o momento merece
- NUNCA comece igual a captions anteriores. Cada uma é ÚNICA.

EXEMPLOS DE ESTRUTURA (varie, NUNCA repita):
- "Nome encontra algo inesperado e a reação é impagável"
- "Um dos momentos mais tensos da live. Conteúdo puro."
- "Quando improviso e talento se encontram, nasce um clipe assim"
- "Os melhores momentos em um compilado que vale cada segundo"

HASHTAGS: {hashtag_guidance_pro}

[SEED DE CRIATIVIDADE: {creativity_seed}]
[ÂNGULO: {chosen_angle}]""",
    }

    persona = PERSONAS.get(options.tone, PERSONAS["Viral"])

    # ── Montar contexto do vídeo ──
    context_parts = []
    if game_name:
        context_parts.append(f"Jogo/Categoria: {game_name}")
    if streamer:
        context_parts.append(f"Canal/Streamer: {streamer}")
    if broadcasters and len(broadcasters) > 1:
        context_parts.append(f"Streamers nos clipes: {', '.join(broadcasters)}")
    if target_type:
        context_parts.append(f"Tipo de alvo: {'Categoria' if target_type == 'category' else 'Canal'}")
    if clip_titles:
        context_parts.append(f"Títulos dos clipes originais: {' | '.join(clip_titles)}")
    if clip_views:
        total_views = sum(clip_views)
        context_parts.append(f"Views combinadas: {total_views}")
    if total_clips:
        context_parts.append(f"Clipes combinados no vídeo: {total_clips}")
    if item.duration_seconds:
        mins = item.duration_seconds // 60
        secs = item.duration_seconds % 60
        context_parts.append(f"Duração do vídeo final: {mins}:{secs:02d}")

    video_context = "\n".join(context_parts) if context_parts else "Sem metadados adicionais."

    length_guide = {
        "short": "Máximo 150 caracteres na caption. Direto, cortante, uma facada de texto.",
        "medium": "150-300 caracteres. Micro-história em 2-3 linhas com gancho + desenvolvimento.",
        "long": "300-500 caracteres. Storytelling completo com contexto, emoção e CTA.",
    }

    # ── Few-shot examples por tom (ancoram formato + qualidade) ──
    FEW_SHOT = {
        "Viral": [
            {"caption": "o bixo morreu 3 vezes seguidas e ainda tava rindo KKKKK esse é o tipo de jogador que eu respeito 💀", "hashtags": ["#fyp", "#twitch", "#gaming", "#fails"]},
            {"caption": "simplesmente a melhor reação que eu já vi numa live. ele NÃO acreditou no que aconteceu", "hashtags": ["#viral", "#twitchclips", "#react"]},
        ],
        "Polêmico": [
            {"caption": "se você acha que isso foi sorte, você nunca jogou na vida. respeita o talento", "hashtags": ["#gaming", "#skill", "#twitch"]},
            {"caption": "todo mundo falando que ele errou mas NINGUÉM teria feito melhor. pode falar", "hashtags": ["#opinião", "#twitch", "#gamer"]},
        ],
        "Engraçado": [
            {"caption": "tutorial completo de como NÃO fazer speedrun em 47 segundos kkkkkk", "hashtags": ["#humor", "#gaming", "#fails", "#twitch"]},
            {"caption": "ele olhou pro boss e o boss olhou de volta. nenhum dos dois sabia o que fazer 💀", "hashtags": ["#gaming", "#meme", "#twitchclips"]},
        ],
        "Profissional": [
            {"caption": "Quando concentração e reflexo se encontram no momento exato. Clipe cirúrgico.", "hashtags": ["#twitch", "#gameplay", "#highlights"]},
            {"caption": "Um daqueles momentos que lembram por que a gente assiste live. Conteúdo genuíno do início ao fim.", "hashtags": ["#livestream", "#twitch", "#conteúdo"]},
        ],
    }

    few_shot_examples = FEW_SHOT.get(options.tone, FEW_SHOT["Viral"])
    few_shot_str = "\n".join([
        f'Exemplo {i+1}: {json.dumps(ex, ensure_ascii=False)}'
        for i, ex in enumerate(few_shot_examples)
    ])

    system_prompt = f"""{persona}

─── MISSÃO ───
Crie UMA descrição para TikTok/Shorts baseada no conteúdo REAL do vídeo abaixo.

TAMANHO: {length_guide.get(options.length, length_guide['short'])}

EXEMPLOS DE OUTPUT (use como referência de FORMATO e QUALIDADE, mas crie algo ORIGINAL):
{few_shot_str}

REGRAS INVIOLÁVEIS:
1. A caption DEVE refletir o que REALMENTE acontece no vídeo. Use a transcrição como fonte primária — cite falas reais, reações específicas, momentos exatos.
2. NUNCA invente eventos, falas ou situações. Se a transcrição diz "ai meu deus", use isso. Se não há transcrição, baseie-se APENAS nos títulos dos clipes.
3. Escreva em PT-BR coloquial e natural (como um brasileiro real escreveria no TikTok).
4. NÃO comece com prefixos de prompt como "hot take:", "opinião impopular:", "neste vídeo...", "veja só...", "confira...". A frase deve ser direta.
5. Responda APENAS em JSON válido: {{"caption": "sua caption aqui", "hashtags": ["#tag1", "#tag2"]}}
{f"6. Gere entre 3 e 5 hashtags (MÁXIMO 5). Use APENAS tags relevantes ao conteúdo REAL do vídeo. Se a categoria é '{game_name or 'desconhecida'}', as hashtags devem refletir ESSE contexto. NUNCA inclua #gaming se o conteúdo não é sobre jogos (ex: Just Chatting, IRL, react)." if options.include_hashtags else "6. NÃO inclua hashtags, retorne lista vazia"}
7. A caption deve funcionar como GANCHO — quem lê tem que querer assistir o vídeo. Foque no momento mais impactante/engraçado/tenso.
8. MENCIONE o streamer pelo nome ({streamer}) de forma natural. Ex: "{streamer} perdeu a cabeça quando..."
9. Se o clipe tem uma reação forte (grito, riso, susto), DESTAQUE isso na caption.
10. NUNCA use aspas ao redor da caption inteira. Escreva como texto direto.
11. OBRIGATÓRIO: Sua caption deve ser COMPLETAMENTE DIFERENTE de qualquer outra que você já tenha escrito. Varie a estrutura, o ângulo narrativo, e as primeiras palavras.
"""

    instruction = options.instruction or f"Escreva a descrição perfeita para esse vídeo no tom {options.tone}"

    user_prompt = f"""[INSTRUÇÃO DO CURADOR] {instruction}

[CONTEXTO DO VÍDEO]
{video_context}

[TRANSCRIÇÃO COMPLETA (WHISPER)]
{transcript_text if transcript_text else "(Sem áudio transcrito — baseie-se nos títulos e metadados dos clipes)"}

[DICA] Analise a transcrição com atenção. Identifique o MOMENTO-CHAVE (o pico emocional, a fala mais marcante, a reação mais forte) e construa a caption ao redor desse momento. A caption deve fazer o viewer parar o scroll.

Responda SOMENTE com o JSON. Nenhum texto antes ou depois.
"""

    # ── Chamar Oracle com system/user message separation ──
    try:
        from core.oracle import oracle_client

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = oracle_client.generate_content(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.9,
            max_completion_tokens=2048,
        )

        import json as json_mod
        content = result.text if hasattr(result, 'text') else str(result)

        # Robust JSON parsing with multiple fallback strategies
        parsed = None

        # Strategy 1: Direct JSON parse
        try:
            parsed = json_mod.loads(content)
        except json_mod.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code fence ```json ... ```
        if not parsed:
            import re
            fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if fence_match:
                try:
                    parsed = json_mod.loads(fence_match.group(1))
                except json_mod.JSONDecodeError:
                    pass

        # Strategy 3: Find JSON object with caption key (handles nested braces)
        if not parsed:
            import re
            # Match from {"caption" to the last } that balances
            match = re.search(r'\{[^{}]*"caption"\s*:\s*"[^"]*"[^{}]*\}', content, re.DOTALL)
            if match:
                try:
                    parsed = json_mod.loads(match.group())
                except json_mod.JSONDecodeError:
                    pass

        # Strategy 4: Greedy brace extraction
        if not parsed:
            import re
            match = re.search(r'\{.*"caption".*\}', content, re.DOTALL)
            if match:
                try:
                    parsed = json_mod.loads(match.group())
                except json_mod.JSONDecodeError:
                    pass

        # Strategy 5: Raw text fallback
        if not parsed:
            # Clean up common LLM artifacts
            clean = content.strip()
            if clean.startswith('"') and clean.endswith('"'):
                clean = clean[1:-1]
            parsed = {"caption": clean, "hashtags": []}
            logger.warning(f"Caption fallback to raw text for item #{item_id}")

        caption = parsed.get("caption", "").strip()
        hashtags = parsed.get("hashtags", [])[:5]  # Limite: 3-5 hashtags

        # Clean caption: remove enclosing quotes if LLM added them
        if caption.startswith('"') and caption.endswith('"'):
            caption = caption[1:-1]

        # Persistir no PendingApproval
        item.caption = caption
        item.hashtags = hashtags
        item.caption_generated = True
        db.commit()

        logger.info(f"Caption gerada via Oracle para item #{item_id}: {len(caption)} chars, {len(hashtags)} tags")

        return {
            "caption": caption,
            "hashtags": hashtags,
            "model": "llama-3.3-70b-versatile",
            "tone": options.tone,
        }

    except Exception as e:
        logger.error(f"Erro ao gerar caption para item #{item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar caption: {str(e)}")


# ─── POST /retry-failed — Retenta uploads falhados ──────────────────────

@router.post("/retry-failed")
async def retry_failed(db: Session = Depends(get_db)):
    """
    Retenta todos os uploads falhados na VideoQueue (max 3 tentativas por item).
    """
    try:
        from core.auto_scheduler import retry_failed_uploads
        result = await retry_failed_uploads(db)
        return result
    except Exception as e:
        logger.error(f"Erro ao retentar uploads falhados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── DELETE /reject/{id} ─────────────────────────────────────────────────

@router.delete("/reject/{item_id}")
def reject_item(item_id: int, db: Session = Depends(get_db)):
    """
    Rejeita um vídeo pendente.
    Remove do DB e aplica garbage collection no arquivo físico.
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    video_path = item.video_path

    # Remover do DB
    db.delete(item)
    db.commit()

    # Garbage collection: remover arquivo físico
    if video_path and os.path.exists(video_path):
        try:
            os.remove(video_path)
            logger.info(f"🗑️ Arquivo removido: {video_path}")
        except OSError as e:
            logger.warning(f"Falha ao remover arquivo {video_path}: {e}")

    logger.info(f"❌ Item #{item_id} rejeitado e removido")

    return {"message": "Vídeo rejeitado e removido com sucesso"}


# ─── POST /reorder/{id} ─────────────────────────────────────────────────

class ReorderRequest(BaseModel):
    order: List[int]  # Nova ordem dos clips via indices [2, 0, 1]

@router.post("/reorder/{item_id}")
async def reorder_item(item_id: int, body: ReorderRequest, db: Session = Depends(get_db)):
    """
    Reordena os clipes de um job pendente e re-agenda o processamento.
    Aceita uma lista de indices representando a nova ordem desejada.
    Ex: [2, 0, 1] = clip 2 primeiro, clip 0 segundo, clip 1 terceiro.
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    from core.clipper.models import ClipJob
    job = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job associado não encontrado")

    clip_count = len(job.clip_urls) if job.clip_urls else 0
    if clip_count <= 1:
        raise HTTPException(status_code=400, detail="Este job não possui clipes suficientes para reordenar.")

    # Validar que order contém exatamente os indices corretos
    if sorted(body.order) != list(range(clip_count)):
        raise HTTPException(status_code=400, detail=f"Ordem inválida. Esperado permutação de {list(range(clip_count))}, recebido {body.order}")

    # Para o front-end, body.order contém a lista de 'index' originais dos clipes na ordem desejada
    # Precisamos mapear o 'index' (ID lógico) para a posição atual no array (ID físico)
    if not job.clip_metadata:
        raise HTTPException(status_code=400, detail="Sem metadata para mapear ordem")
        
    current_positions = { c.get('index', i): i for i, c in enumerate(job.clip_metadata) }
    
    try:
        new_positions = [current_positions[orig_idx] for orig_idx in body.order]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Índice original {e} não encontrado")

    # Aplicar reordenação nas listas paralelas baseado nas posições absolutas corretas
    def reorder_list(lst, pos_array):
        if not lst:
            return lst
        return [lst[pos] for pos in pos_array]

    job.clip_urls = reorder_list(job.clip_urls, new_positions)
    job.clip_metadata = reorder_list(job.clip_metadata, new_positions)
    job.clip_local_paths = reorder_list(job.clip_local_paths, new_positions)
    job.whisper_result = reorder_list(job.whisper_result, new_positions)

    # Resetar o status do job para pending para ser pego pelo Worker
    job.status = "pending"
    job.progress_pct = 0
    job.current_step = "Re-agendado com nova ordem de clipes"
    job.output_path = None
    
    # Remover o arquivo físico gerado na primeira tentativa
    if item.video_path and os.path.exists(item.video_path):
        try:
            os.remove(item.video_path)
            logger.info(f"🗑️ Arquivo anterior do job #{job.id} removido: {item.video_path}")
        except OSError as e:
            logger.warning(f"Falha ao remover arquivo antigo do job #{job.id}: {e}")

    # Remover o registro do PendingApproval, pois ele não é mais válido
    db.delete(item)
    db.commit()

    # Re-enfileirar o job no ARQ
    from core.queue_manager import QueueManager
    try:
        pool = await QueueManager.get_pool()
        await pool.enqueue_job("process_clip_job", job.id, _queue_name="clipper:queue")
        logger.info(f"🔀 Job #{job.id} re-enfileirado com nova ordem de clipes: {body.order}")
    except Exception as e:
        logger.error(f"Erro ao re-enfileirar job #{job.id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar tarefa para processamento")

    return {
        "message": "Ordem dos clipes atualizada com sucesso. O vídeo será recriado.",
        "job_id": job.id,
    }

class ReprocessRequest(BaseModel):
    layout_mode_overrides: Optional[dict[str, str]] = None


@router.post("/reprocess/{item_id}")
async def reprocess_item(item_id: int, req: Optional[ReprocessRequest] = None, db: Session = Depends(get_db)):
    """
    Reprocessa um vídeo inteiro: reseta o job para pending e re-enfileira.
    Opcionalmente recebe overrides de layout por clipe.
    O vídeo antigo é removido e o PendingApproval é deletado.
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    from core.clipper.models import ClipJob
    job = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job associado não encontrado")

    # Remover arquivo físico do vídeo antigo
    if item.video_path and os.path.exists(item.video_path):
        try:
            os.remove(item.video_path)
            logger.info(f"🗑️ Arquivo anterior do job #{job.id} removido: {item.video_path}")
        except OSError as e:
            logger.warning(f"Falha ao remover arquivo antigo do job #{job.id}: {e}")

    # Resetar job para pending
    job.status = "pending"
    job.progress_pct = 0
    job.current_step = "Reprocessando (solicitado pelo usuário)"
    job.output_path = None
    job.error_message = None
    if req and req.layout_mode_overrides:
        job.layout_mode_overrides = req.layout_mode_overrides
    else:
        # Se não enviou nada, podemos manter os antigos ou limpar. Melhor limpar para garantir.
        job.layout_mode_overrides = {}

    # Deletar PendingApproval
    db.delete(item)
    db.commit()

    # Re-enfileirar no Redis
    from core.queue_manager import QueueManager
    try:
        pool = await QueueManager.get_pool()
        await pool.enqueue_job("process_clip_job", job.id, _queue_name="clipper:queue")
        logger.info(f"🔄 Job #{job.id} re-enfileirado para reprocessamento completo")
    except Exception as e:
        logger.error(f"Erro ao re-enfileirar job #{job.id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar tarefa para processamento")

    return {
        "message": "Vídeo enviado para reprocessamento. Aguarde na esteira.",
        "job_id": job.id,
    }


class RemoveClipRequest(BaseModel):
    clip_index: int


@router.post("/remove-clip/{item_id}")
async def remove_clip_and_reprocess(item_id: int, body: RemoveClipRequest, db: Session = Depends(get_db)):
    """
    Remove um clip específico de um job e reprocessa o vídeo sem ele.
    Útil quando um clip tem problema de áudio ou qualidade.
    """
    item = db.query(PendingApproval).filter(PendingApproval.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    from core.clipper.models import ClipJob
    job = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job associado não encontrado")

    clip_count = len(job.clip_urls) if job.clip_urls else 0
    if clip_count <= 1:
        raise HTTPException(status_code=400, detail="Não é possível remover o único clip do job.")

    if body.clip_index < 0 or body.clip_index >= clip_count:
        raise HTTPException(status_code=400, detail=f"Índice inválido. Deve ser entre 0 e {clip_count - 1}.")

    removed_title = "?"
    if job.clip_metadata and body.clip_index < len(job.clip_metadata):
        removed_title = job.clip_metadata[body.clip_index].get("title", "?")

    # Remover clip de todos os arrays paralelos
    def remove_at(lst, idx):
        if not lst or idx >= len(lst):
            return lst
        return lst[:idx] + lst[idx + 1:]

    job.clip_urls = remove_at(job.clip_urls, body.clip_index)
    job.clip_metadata = remove_at(job.clip_metadata, body.clip_index)
    job.clip_local_paths = remove_at(job.clip_local_paths, body.clip_index)
    job.whisper_result = remove_at(job.whisper_result, body.clip_index)

    # Remover arquivo físico do vídeo antigo
    if item.video_path and os.path.exists(item.video_path):
        try:
            os.remove(item.video_path)
        except OSError:
            pass

    # Resetar job
    job.status = "pending"
    job.progress_pct = 0
    job.current_step = f"Reprocessando sem clip '{removed_title}'"
    job.output_path = None
    job.error_message = None

    db.delete(item)
    db.commit()

    # Re-enfileirar
    from core.queue_manager import QueueManager
    try:
        pool = await QueueManager.get_pool()
        await pool.enqueue_job("process_clip_job", job.id, _queue_name="clipper:queue")
        logger.info(f"🔄 Job #{job.id} re-enfileirado sem clip #{body.clip_index} ('{removed_title}')")
    except Exception as e:
        logger.error(f"Erro ao re-enfileirar job #{job.id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar tarefa para processamento")

    return {
        "message": f"Clip '{removed_title}' removido. Vídeo será reprocessado com {clip_count - 1} clips.",
        "job_id": job.id,
        "remaining_clips": clip_count - 1,
    }


# ─── POST /revert/{schedule_item_id} — Reverter agendamento para aprovação ──

@router.post("/revert/{schedule_item_id}")
async def revert_to_approval(schedule_item_id: int, db: Session = Depends(get_db)):
    """
    Reverte um vídeo agendado de volta para a fila de aprovação.
    - Deleta o ScheduleItem do scheduler
    - Move arquivo de /data/approved/ para /data/pending/
    - Reseta PendingApproval.status para 'pending'
    - Limpa VideoQueue vinculado
    """
    from core.models import ScheduleItem, VideoQueue

    item = db.query(ScheduleItem).filter(ScheduleItem.id == schedule_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    if item.status in ("posted", "processing"):
        raise HTTPException(status_code=400, detail=f"Não é possível reverter: status '{item.status}'")

    video_path = item.video_path
    profile_slug = item.profile_slug

    # 1. Mover arquivo de approved/ de volta para pending/
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    APPROVED_DIR = os.path.join(BASE_DIR, "data", "approved")
    PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")
    os.makedirs(PENDING_DIR, exist_ok=True)

    filename = os.path.basename(video_path) if video_path else None
    moved = False
    if filename:
        approved_path = os.path.join(APPROVED_DIR, filename)
        pending_path = os.path.join(PENDING_DIR, filename)
        if os.path.exists(approved_path):
            import shutil
            shutil.move(approved_path, pending_path)
            moved = True
            logger.info(f"Revert: movido {filename} de approved/ para pending/")
            # Mover metadata JSON se existir
            json_name = os.path.splitext(filename)[0] + ".json"
            json_approved = os.path.join(APPROVED_DIR, json_name)
            if os.path.exists(json_approved):
                shutil.move(json_approved, os.path.join(PENDING_DIR, json_name))
        elif os.path.exists(video_path):
            # Arquivo já está em outro lugar, copiar para pending
            import shutil
            shutil.copy2(video_path, pending_path)
            moved = True

    # 2. Encontrar e resetar PendingApproval vinculado
    pending_item = None
    # Tentar via VideoQueue -> clip_job_id ou via video_path
    vq = db.query(VideoQueue).filter(VideoQueue.schedule_item_id == schedule_item_id).first()
    if vq:
        # Buscar PendingApproval pelo video_path do VideoQueue
        pending_item = db.query(PendingApproval).filter(
            PendingApproval.video_path.contains(filename) if filename else False
        ).first()
        vq.schedule_item_id = None
        vq.status = "cancelled"

    if not pending_item and filename:
        # Buscar por qualquer path que contenha o filename
        all_pending = db.query(PendingApproval).filter(PendingApproval.status == "approved").all()
        for p in all_pending:
            if p.video_path and os.path.basename(p.video_path) == filename:
                pending_item = p
                break

    if pending_item:
        pending_item.status = "pending"
        # Atualizar path para o novo local em pending/
        if moved and filename:
            pending_item.video_path = os.path.join(PENDING_DIR, filename)
        logger.info(f"Revert: PendingApproval #{pending_item.id} resetado para 'pending'")

    # 3. Deletar ScheduleItem
    db.delete(item)
    db.commit()

    logger.info(f"Revert: ScheduleItem #{schedule_item_id} deletado, vídeo devolvido à curadoria")

    return {
        "message": "Agendamento revertido. Vídeo devolvido à fila de aprovação.",
        "schedule_item_id": schedule_item_id,
        "pending_approval_reset": pending_item.id if pending_item else None,
        "file_moved": moved,
    }
