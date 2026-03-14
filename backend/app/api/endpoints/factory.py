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
import asyncio
import logging
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
    available_profiles: Optional[List[dict]] = None
    clips: Optional[List[ClipDetail]] = None  # Individual clip metadata for reordering


# ─── Helpers ─────────────────────────────────────────────────────────────

def _resolve_profile_for_approval(item: PendingApproval, db: Session, profile_slug: Optional[str] = None) -> "Profile":
    """
    Resolve qual Profile usar para agendar o video aprovado.

    Prioridade:
    1. profile_slug explicito (frontend escolheu)
    2. Profile vinculado ao Army do TwitchTarget do job
    3. Primeiro Profile ativo como fallback
    """
    # 1. Slug explicito
    if profile_slug:
        profile = db.query(Profile).filter(Profile.slug == profile_slug, Profile.active == True).first()
        if profile:
            return profile

    # 2. Via cadeia: ClipJob → TwitchTarget → army_id → Army.profiles
    if item.clip_job_id:
        from core.clipper.models import ClipJob, TwitchTarget
        job = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first()
        if job and job.target_id:
            target = db.query(TwitchTarget).filter(TwitchTarget.id == job.target_id).first()
            if target and target.army_id:
                army = db.query(Army).filter(Army.id == target.army_id).first()
                if army and army.profiles:
                    # Pegar o primeiro profile ativo do army
                    for p in army.profiles:
                        if p.active:
                            return p

    # 3. Fallback: primeiro profile ativo
    profile = db.query(Profile).filter(Profile.active == True).first()
    return profile


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
        # Resolver army_id via ClipJob → TwitchTarget
        target_army_id = None
        if item.clip_job_id:
            from core.clipper.models import ClipJob, TwitchTarget
            job = db.query(ClipJob).filter(ClipJob.id == item.clip_job_id).first()
            if job and job.target_id:
                target = db.query(TwitchTarget).filter(TwitchTarget.id == job.target_id).first()
                if target:
                    target_army_id = target.army_id

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

        # Resolver profile inteligentemente
        profile = _resolve_profile_for_approval(item, db, body.profile_slug)
        if not profile:
            raise HTTPException(status_code=400, detail="Nenhum perfil ativo encontrado para agendamento")

        # Horários padrão de publicação
        schedule_hours = body.schedule_hours or [12, 18]

        # Montar caption final (sem hashtags — o uploader insere as hashtags)
        final_caption = item.caption or item.title or ""
        final_hashtags = item.hashtags or []

        # 1. Inserir na Smart Queue
        queue_items = create_queue(
            profile_slug=profile.slug,
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

        scheduled_time = None
        from core.models import ScheduleItem

        if body.schedule_mode == "specific" and body.schedule_date and body.schedule_time:
            # Modo específico: agendar para data/hora exata
            hour, minute = map(int, str(body.schedule_time).split(":"))
            target_dt = datetime.fromisoformat(str(body.schedule_date)).replace(
                hour=hour, minute=minute, second=0
            )
            # Criar ScheduleItem diretamente com o horário escolhido
            sched_item = ScheduleItem(
                profile_slug=profile.slug,
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
            scheduled_time = target_dt.isoformat()
            result = {"scheduled": 1, "failed": 0, "queued_remaining": 0}

        elif body.schedule_mode == "now":
            # Modo imediato: próximo slot em 1 minuto (scheduler polls a cada 30s)
            now = datetime.now(SP_TZ)
            target_dt = (now + timedelta(minutes=1)).replace(tzinfo=None)
            # Criar ScheduleItem para execução em ~1 minuto
            sched_item = ScheduleItem(
                profile_slug=profile.slug,
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
            scheduled_time = target_dt.isoformat()
            result = {"scheduled": 1, "failed": 0, "queued_remaining": 0}

        else:
            # Modo smart (padrão): distribuição automática via calculate_next_slots
            result = await schedule_next_batch(
                profile_slug=profile.slug,
                batch_size=1,
                db=db,
            )

        # 3. Marcar como aprovado
        item.status = "approved"
        db.commit()

        if not scheduled_time and queue_items and hasattr(queue_items[0], 'scheduled_at') and queue_items[0].scheduled_at:
            scheduled_time = queue_items[0].scheduled_at.isoformat()

        logger.info(f"Item #{item_id} aprovado [{body.schedule_mode}] -> perfil @{profile.slug} | resultado: {result}")

        return {
            "message": "Vídeo aprovado e inserido na Smart Queue",
            "profile": profile.slug,
            "schedule_mode": body.schedule_mode,
            "scheduled_time": scheduled_time,
            "queue_result": result,
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
                    if not streamer and target.channel_name:
                        streamer = target.channel_name

    # ── Personas UX Writer por Tom ──
    PERSONAS = {
        "Viral": """Você é a LARI, copywriter de 23 anos que vive de TikTok em São Paulo.
Você entende o algoritmo como ninguém. Sua especialidade é criar ganchos que prendem nos primeiros 0.5s de leitura.

ESTILO DE ESCRITA:
- Frases curtas e cortantes, como se fosse uma legenda de meme
- Use gírias BR atuais: "slk", "mlk", "simplesmente", "EU QUANDO...", "pov:", "nobody:", "a cara dele kkk"
- Crie FOMO (Fear Of Missing Out): faça a pessoa sentir que PRECISA assistir
- Use caps lock estratégico para ênfase (não em tudo, em 1-2 palavras chave)
- Máximo 2-3 linhas. Se precisar de mais, cada linha é um gancho separado
- Pode usar emoji com moderação (1-2 no máximo, nunca mais de 3)

EXEMPLOS DO SEU ESTILO:
- "ele simplesmente DESISTIU no meio do boss kkkk"
- "a reação quando ele viu o plot twist 💀"
- "eu jogando RE: Requiem vs o streamer jogando RE: Requiem"
- "ninguém tava preparado pra isso"

HASHTAGS:
- Mix de trending (#fyp #viral #gaming) + nicho específico (#residentevil #twitchbr)
- Sempre inclua #fyp ou #fy e #gaming se for gameplay
- 3-5 hashtags, priorizando alcance depois nicho""",

        "Polêmico": """Você é o RAFA, creator de 27 anos que faz react e gaming polêmico.
Seu conteúdo gera debate nos comentários. Você sabe que engajamento negativo também é engajamento.

ESTILO DE ESCRITA:
- Faça afirmações FORTES e opinativas sobre o que acontece no clipe
- Use perguntas retóricas provocativas: "vocês realmente acham que isso é skill?"
- Tome um lado, nunca fique em cima do muro
- Provoque a audiência a discordar: "prova que eu tô errado nos comentários"
- NUNCA use prefixos de prompt como "hot take:", "opinião impopular:", "unpopular opinion:" — esses são marcadores de prompt e não devem aparecer no texto final
- Polêmico NÃO é tóxico — é assertivo, confiante, desafiador
- A frase deve ser direta e natural, como se fosse um comentário real

EXEMPLOS DO SEU ESTILO:
- "esse cara é o MELHOR player de RE e vocês não estão prontos pra essa conversa"
- "se você morreu nessa parte, desinstala o jogo"
- "a comunidade BR de Twitch carrega a gringa e isso é FATO"
- "vocês tão dormindo nesse streamer e não sabem"

HASHTAGS:
- Mix de tags do game e da comunidade
- 3-5 hashtags, diretas e provocativas""",

        "Engraçado": """Você é o DUDU, comediante digital de 25 anos, especialista em humor gaming BR.
Seu forte é referência de meme, auto-depreciação e timing cômico em texto.

ESTILO DE ESCRITA:
- Humor de observação: descreva a cena de um jeito inesperado
- Auto-depreciação do viewer: "eu tentando fazer isso: 🤡"
- Referências a memes BR atuais (use com naturalidade, não force)
- Narração cômica em terceira pessoa: "ele realmente achou que ia dar certo"
- Use "kkkkk" ou "KKKK" no lugar certo (não em excesso)
- Setup → Punchline: primeira linha cria expectativa, segunda quebra

EXEMPLOS DO SEU ESTILO:
- "o bicho viu o zumbi e escolheu a opção 'correr gritando' kkkkk"
- "tutorial de como NÃO jogar Resident Evil em 30 segundos"
- "eu: vou jogar de boa sem gritar / o jogo: 👁️👄👁️"
- "streamer: 'tá tranquilo' / narrador: não estava tranquilo"

HASHTAGS:
- Tags de humor: #humor #meme #kkkk #gaming #engraçado
- Tags do jogo para alcance
- 3-5 hashtags, tom leve e divertido""",

        "Profissional": """Você é a ANA, produtora de conteúdo gaming de 30 anos com background em jornalismo.
Seu conteúdo é informativo, editorial e respeitado pela comunidade.

ESTILO DE ESCRITA:
- Tom de curadoria: você está apresentando um momento relevante
- Contextualize o clipe: o que aconteceu, por que importa, o que torna especial
- Linguagem clara e polida, sem gírias excessivas (mas não formal demais)
- Pode incluir dado concreto: views, duração, nome do streamer
- Estrutura: contexto breve → destaque do momento → call-to-action sutil
- Não use caps lock nem emoji

EXEMPLOS DO SEU ESTILO:
- "Cellbit encontra uma planta durante a gameplay de RE: Requiem — a reação é ouro puro"
- "Um dos momentos mais tensos da live de ontem. Resident Evil entregando como sempre."
- "Compilado dos melhores clipes da semana na categoria RE: Requiem"
- "Quando o game design encontra o improviso do streamer, momentos como esse nascem"

HASHTAGS:
- Tags profissionais: #gaming #twitch #gameplay #streamer
- Tags do jogo completas: #ResidentEvil #RERequiem
- Tags de curadoria: #melhoresclipes #destaque
- 3-5 hashtags, tom editorial""",
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

    system_prompt = f"""{persona}

─── MISSÃO ───
Crie UMA descrição para TikTok/Shorts baseada no conteúdo REAL do vídeo abaixo.

TAMANHO: {length_guide.get(options.length, length_guide['short'])}

REGRAS INVIOLÁVEIS:
1. A caption DEVE refletir o que REALMENTE acontece no vídeo. Use a transcrição como fonte primária — cite falas reais, reações específicas, momentos exatos.
2. NUNCA invente eventos, falas ou situações. Se a transcrição diz "ai meu deus", use isso. Se não há transcrição, baseie-se APENAS nos títulos dos clipes.
3. Escreva em PT-BR coloquial e natural (como um brasileiro real escreveria no TikTok).
4. NÃO comece com prefixos de prompt como "hot take:", "opinião impopular:", "unpopular opinion:", "neste vídeo...", "veja só...", "confira...". A frase deve ser direta.
5. Responda APENAS em JSON válido: {{"caption": "sua caption aqui", "hashtags": ["#tag1", "#tag2"]}}
{"6. Gere entre 3 e 5 hashtags (MÁXIMO 5). Misture alcance (#fyp #gaming) com nicho (#" + game_name.lower().replace(' ', '').replace(':', '') + ")" if options.include_hashtags else "6. NÃO inclua hashtags, retorne lista vazia"}
7. A caption deve funcionar como GANCHO — quem lê tem que querer assistir o vídeo. Foque no momento mais impactante/engraçado/tenso.
8. MENCIONE o streamer pelo nome ({streamer}) de forma natural. Ex: "{streamer} perdeu a cabeça quando..."
9. Se o clipe tem uma reação forte (grito, riso, susto), DESTAQUE isso na caption.
10. NUNCA use aspas ao redor da caption inteira. Escreva como texto direto.
"""

    instruction = options.instruction or f"Escreva a descrição perfeita para esse vídeo no tom {options.tone}"

    prompt = f"""[INSTRUÇÃO DO CURADOR] {instruction}

[CONTEXTO DO VÍDEO]
{video_context}

[TRANSCRIÇÃO COMPLETA (WHISPER)]
{transcript_text if transcript_text else "(Sem áudio transcrito — baseie-se nos títulos e metadados dos clipes)"}

[DICA] Analise a transcrição com atenção. Identifique o MOMENTO-CHAVE (o pico emocional, a fala mais marcante, a reação mais forte) e construa a caption ao redor desse momento. A caption deve fazer o viewer parar o scroll.
"""

    # ── Chamar Oracle ──
    try:
        from core.oracle import oracle_client

        full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"

        result = oracle_client.generate_content(
            prompt_input=full_prompt,
            model="llama-3.3-70b-versatile",
            temperature=0.85,
        )

        import json
        content = result.text if hasattr(result, 'text') else str(result)

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{[^{}]*"caption"[^{}]*\}', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                parsed = {"caption": content.strip(), "hashtags": []}

        caption = parsed.get("caption", "")
        hashtags = parsed.get("hashtags", [])

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

    # Aplicar reordenação em todos os arrays paralelos
    def reorder_list(lst, order):
        if not lst:
            return lst
        return [lst[i] for i in order]

    job.clip_urls = reorder_list(job.clip_urls, body.order)
    job.clip_metadata = reorder_list(job.clip_metadata, body.order)
    job.clip_local_paths = reorder_list(job.clip_local_paths, body.order)
    job.whisper_result = reorder_list(job.whisper_result, body.order)

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
