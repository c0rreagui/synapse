"""
Clipper Monitor - CronJob de Monitoramento da Twitch API
=========================================================

Consulta periodicamente a API da Twitch buscando Top Clips dos canais
cadastrados em TwitchTarget. Quando encontra clipes novos, enfileira
ClipJobs para processamento.

Requisitos:
    - TWITCH_CLIENT_ID e TWITCH_CLIENT_SECRET no .env
    - A Twitch API usa OAuth2 Client Credentials (sem login de usuario)

Referencia da API:
    GET https://api.twitch.tv/helix/clips
    Params: broadcaster_id, first, started_at, ended_at
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from zoneinfo import ZoneInfo

import httpx
from arq import create_pool
from arq.connections import RedisSettings

from core.database import safe_session
from core.clipper.models import TwitchTarget, ClipJob
from core.config import TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET

logger = logging.getLogger("ClipperMonitor")

SP_TZ = ZoneInfo("America/Sao_Paulo")

# ─── Twitch OAuth2 ──────────────────────────────────────────────────────

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_HELIX_URL = "https://api.twitch.tv/helix"

_cached_token: Optional[str] = None
_token_expires_at: float = 0


async def _get_twitch_token(client: httpx.AsyncClient) -> str:
    """
    Obtem ou reutiliza um token OAuth2 Client Credentials da Twitch.
    Tokens duram ~60 dias, entao cacheamos em memoria.
    """
    global _cached_token, _token_expires_at

    if _cached_token and _token_expires_at > datetime.now(timezone.utc).timestamp():
        return _cached_token

    resp = await client.post(
        TWITCH_TOKEN_URL,
        params={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    _cached_token = data["access_token"]
    _token_expires_at = datetime.now(timezone.utc).timestamp() + data.get("expires_in", 3600) - 300
    logger.info("Token Twitch OAuth2 obtido/renovado com sucesso.")
    return _cached_token


# ─── Resolucao de Canal ─────────────────────────────────────────────────

def _extract_target_info(url: str) -> tuple[str, str]:
    """
    Retorna uma tupla (target_type, slug_or_name)
    Aceita formatos:
        https://www.twitch.tv/directory/category/just-chatting/clips -> ('category', 'just-chatting')
        https://twitch.tv/gaules -> ('channel', 'gaules')
        gaules -> ('channel', 'gaules')
    """
    import urllib.parse
    url = urllib.parse.unquote(url).strip()
    url = url.split("?")[0].rstrip("/")

    if "/category/" in url:
        parts = url.split("/category/")[-1].split("/")
        return "category", parts[0]
    elif "twitch.tv/" in url:
        parts = url.split("twitch.tv/")[-1].split("/")
        return "channel", parts[0].lower()
    elif "/" in url:
        parts = url.split("/")
        target = parts[-1].lower()
        if target == "clips" and len(parts) > 1:
            target = parts[-2].lower()
        return "channel", target
    return "channel", url.lower()


async def _resolve_broadcaster_info(
    client: httpx.AsyncClient, token: str, channel_name: str
) -> Optional[Dict[str, str]]:
    """Resolve o nome do canal para broadcaster_id e profile_image_url via Twitch Helix API."""
    resp = await client.get(
        f"{TWITCH_HELIX_URL}/users",
        params={"login": channel_name},
        headers={
            "Client-Id": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as e:
        logger.warning(f"Erro HTTP na Twitch API ao buscar canal '{channel_name}': {e}")
        return None

    users = data.get("data", [])
    if not users:
        logger.warning(f"Canal '{channel_name}' nao encontrado na Twitch.")
        return None

    return {
        "id": users[0]["id"],
        "name": users[0].get("display_name", channel_name),
        "profile_image_url": users[0].get("profile_image_url", ""),
        "offline_image_url": users[0].get("offline_image_url", "")
    }

async def _resolve_category_info(
    client: httpx.AsyncClient, token: str, category_slug: str
) -> Optional[Dict[str, str]]:
    """Resolve o slug da categoria para category_id via Twitch Helix API."""
    query = category_slug.replace("-", " ")
    resp = await client.get(
        f"{TWITCH_HELIX_URL}/search/categories",
        params={"query": query},
        headers={
            "Client-Id": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as e:
        logger.warning(f"Erro HTTP na Twitch API ao buscar categoria '{query}': {e}")
        return None

    categories = data.get("data", [])
    if not categories:
        logger.warning(f"Categoria '{query}' nao encontrada na Twitch.")
        return None

    # Priorizar match exato pelo nome (case-insensitive)
    best = None
    for cat in categories:
        if cat["name"].lower() == query.lower():
            best = cat
            break
    if not best:
        # Fallback: match pelo slug (ex: "just-chatting" -> "Just Chatting")
        for cat in categories:
            if cat["name"].lower().replace(" ", "-") == category_slug.lower():
                best = cat
                break
    if not best:
        best = categories[0]  # Último fallback: primeiro resultado

    return {
        "id": best["id"],
        "name": best["name"],
        "box_art_url": best.get("box_art_url", "").replace("{width}", "285").replace("{height}", "380")
    }


# ─── Busca de Clipes ────────────────────────────────────────────────────

def _format_twitch_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

async def fetch_top_clips(
    client: httpx.AsyncClient,
    token: str,
    target_id: str,
    target_type: str = "channel",
    hours_lookback: int = 24,
    max_clips: int = 100,
    min_views: int = 100,
) -> List[Dict[str, Any]]:
    """
    Busca os Top Clips de um target (channel ou category) nas ultimas N horas.
    Usa paginacao cursor-based para extrair o maximo possivel da API Twitch (first=100).
    """
    now = datetime.now(timezone.utc)
    started_at = _format_twitch_time(now - timedelta(hours=hours_lookback))
    ended_at = _format_twitch_time(now)

    all_clips: List[Dict] = []
    cursor = None
    max_pages = 5  # Safety: no maximo 5 paginas (500 clips)
    page_size = min(100, max_clips)  # Twitch API max = 100 per request

    page_count = 0
    for _ in range(max_pages):
        page_count += 1
        params: Dict[str, Any] = {
            "first": page_size,
            "started_at": started_at,
            "ended_at": ended_at,
        }

        if target_type in ["game", "category"]:
            params["game_id"] = target_id
        else:
            params["broadcaster_id"] = target_id

        if cursor:
            params["after"] = cursor

        try:
            resp = await client.get(
                f"{TWITCH_HELIX_URL}/clips",
                params=params,
                headers={
                    "Client-Id": TWITCH_CLIENT_ID,
                    "Authorization": f"Bearer {token}",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            # SYN-128: Capturar headers de rate limit para o scheduler
            try:
                from core.clipper.scheduler import rate_limit
                rate_limit.update_from_headers(dict(resp.headers))
            except Exception:
                pass  # Scheduler pode não estar importado em testes
        except httpx.HTTPError as e:
            logger.warning(f"Erro HTTP na Twitch API ao buscar clipes (pag {page_count}): {e}")
            break

        page_clips = data.get("data", [])
        all_clips.extend(page_clips)

        # Parar se nao houver mais paginas ou ja temos clips suficientes
        cursor = data.get("pagination", {}).get("cursor")
        if not cursor or len(all_clips) >= max_clips:
            break

        await asyncio.sleep(0.5)  # Respeitar rate limit entre paginas

    logger.info(f"Twitch API retornou {len(all_clips)} clipes brutos em {page_count} pagina(s)")

    # Filtrar por idioma (pt/pt-br) e minimo de views, ordenando por view_count desc
    filtered = [
        c for c in all_clips 
        if c.get("language", "").startswith("pt") and c.get("view_count", 0) >= min_views
    ]
    filtered.sort(key=lambda c: c.get("view_count", 0), reverse=True)

    # Buscar nomes dos jogos em bulk
    game_names = {}
    game_ids = list(set([c.get("game_id") for c in filtered if c.get("game_id")]))
    if game_ids:
        # Busca em lotes de 100
        for i in range(0, len(game_ids), 100):
            chunk = game_ids[i:i+100]
            params = [("id", gid) for gid in chunk]
            try:
                resp = await client.get(
                    f"{TWITCH_HELIX_URL}/games",
                    params=params,
                    headers={
                        "Client-Id": TWITCH_CLIENT_ID,
                        "Authorization": f"Bearer {token}",
                    },
                )
                resp.raise_for_status()
                for g in resp.json().get("data", []):
                    game_names[g["id"]] = g["name"]
            except Exception as e:
                logger.warning(f"Erro ao buscar detalhes dos games: {e}")

    # Retornar TODOS os clips qualificados (sem corte artificial)
    results = []
    for clip in filtered:
        results.append({
            "id": clip["id"],
            "url": clip["url"],
            "embed_url": clip.get("embed_url", ""),
            "title": clip.get("title", ""),
            "view_count": clip.get("view_count", 0),
            "duration": clip.get("duration", 0),
            "creator_name": clip.get("creator_name", ""),
            "created_at": clip.get("created_at", ""),
            "thumbnail_url": clip.get("thumbnail_url", ""),
            "game_id": clip.get("game_id", ""),
            "game": game_names.get(clip.get("game_id", ""), ""),
            "broadcaster_name": clip.get("broadcaster_name", ""),
        })

    logger.info(f"{len(results)} clipes passaram no filtro (min_views={min_views})")
    return results


async def register_target(channel_url: str, army_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Cadastra um novo canal ou categoria da Twitch para monitoramento.
    """
    target_type, slug = _extract_target_info(channel_url)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token = await _get_twitch_token(client)
            
            target_name = slug
            broadcaster_id = None
            category_id = None
            profile_image_url = None
            offline_image_url = None

            if target_type == "category":
                info = await _resolve_category_info(client, token, slug)
                if not info:
                    raise ValueError(f"Categoria '{slug}' nao encontrada na Twitch API.")
                category_id = info["id"]
                target_name = info["name"]
                profile_image_url = info["box_art_url"]
            else:
                info = await _resolve_broadcaster_info(client, token, slug)
                if not info:
                    raise ValueError(f"Canal '{slug}' nao encontrado na Twitch API.")
                broadcaster_id = info["id"]
                target_name = info["name"]
                profile_image_url = info["profile_image_url"]
                offline_image_url = info.get("offline_image_url", "")
    except httpx.TimeoutException:
        raise ValueError(f"Timeout ao registrar alvo: {channel_url}. A API da Twitch demorou a responder.")
    except httpx.HTTPError as e:
        raise ValueError(f"Erro de HTTP ao registrar alvo: {e}")

    with safe_session() as db:
        # Verifica duplicata baseada no type
        query = db.query(TwitchTarget).filter(TwitchTarget.target_type == target_type)
        if target_type == "category":
            query = query.filter(TwitchTarget.category_id == category_id)
        else:
            query = query.filter(TwitchTarget.broadcaster_id == broadcaster_id)
            
        existing = query.first()

        if existing:
            if not existing.active:
                existing.active = True
            
            existing.channel_name = target_name
            existing.profile_image_url = profile_image_url
            existing.offline_image_url = offline_image_url
            if army_id is not None:
                existing.army_id = army_id
                
            db.commit()
            return {
                "id": existing.id,
                "target_type": existing.target_type,
                "channel_name": existing.channel_name,
                "broadcaster_id": existing.broadcaster_id,
                "category_id": existing.category_id,
                "profile_image_url": existing.profile_image_url,
                "min_clip_views": existing.min_clip_views,
                "max_clips_per_check": existing.max_clips_per_check,
                "status": "already_registered",
            }

        lookback = 24 if target_type == 'channel' else 168
        
        target = TwitchTarget(
            channel_url=channel_url.strip(),
            channel_name=target_name,
            target_type=target_type,
            broadcaster_id=broadcaster_id,
            category_id=category_id,
            profile_image_url=profile_image_url,
            offline_image_url=offline_image_url,
            army_id=army_id,
            lookback_hours=lookback,
            active=True
        )
        db.add(target)
        db.commit()
        db.refresh(target)

        return {
            "id": target.id,
            "target_type": target.target_type,
            "channel_name": target.channel_name,
            "broadcaster_id": target.broadcaster_id,
            "category_id": target.category_id,
            "profile_image_url": target.profile_image_url,
            "min_clip_views": target.min_clip_views,
            "max_clips_per_check": target.max_clips_per_check,
            "status": "created",
        }


# ─── Loop Principal do CronJob ──────────────────────────────────────────

async def check_target(target_id: int) -> Optional[int]:
    """
    Verifica um unico TwitchTarget por novos clipes.
    Se encontrar, cria um ClipJob e retorna seu ID.

    SYN-127 — Arquitetura Híbrida:
      - Channel targets: busca normal por broadcaster_id (sem mudança)
      - Category targets:
          Fluxo A (Whitelist): Se há streamers mapeados, busca clipes de cada um
          Fluxo B (Fallback): Se whitelist vazia, deep pagination por categoria
    """
    with safe_session() as db:
        target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if not target or not target.active:
            return None

        broadcaster_id = target.broadcaster_id
        category_id = target.category_id
        target_type = target.target_type
        channel_name = target.channel_name
        max_clips = target.max_clips_per_check
        min_views = target.min_clip_views
        lookback_hours = getattr(target, 'lookback_hours', 6) or 6

    # ─── Canal: busca direta (sem mudança) ──────────────────────────────
    if target_type != "category":
        twitch_target_id = broadcaster_id
        if not twitch_target_id:
            logger.warning(f"Target {target_id} sem broadcaster_id. Pulando.")
            return None

        async with httpx.AsyncClient(timeout=15) as client:
            token = await _get_twitch_token(client)
            clips = await fetch_top_clips(
                client, token, twitch_target_id,
                target_type="channel",
                hours_lookback=lookback_hours,
                max_clips=max_clips,
                min_views=min_views,
            )

        if not clips:
            _update_target_checked(target_id, found_clips=False)
            logger.info(f"[{channel_name}] Nenhum clipe novo encontrado.")
            return None

        new_clips = _filter_already_processed(target_id, clips)
        if not new_clips:
            _update_target_checked(target_id, found_clips=False)
            logger.info(f"[{channel_name}] Clipes encontrados, mas todos ja processados.")
            return None

        job_ids = await _create_clip_jobs(target_id, channel_name, new_clips)
        return job_ids[0] if job_ids else None

    # ─── Categoria: Arquitetura Híbrida (SYN-127) ──────────────────────
    if not category_id:
        logger.warning(f"Target {target_id} sem category_id. Pulando.")
        return None

    # 1. Rodar o Radar para descobrir streamers (SYN-126)
    from core.clipper.radar import scan_category, get_known_streamers
    try:
        new_found = await scan_category(category_id)
        if new_found:
            logger.info(f"[{channel_name}] Radar descobriu {new_found} novo(s) streamer(s) PT-BR")
    except Exception as e:
        logger.warning(f"[{channel_name}] Erro no radar (continuando com whitelist existente): {e}")

    # 2. Consultar a whitelist
    known = get_known_streamers(category_id)

    if known:
        # ─── Fluxo A: Coleta Cirúrgica (Whitelist) ─────────────────
        logger.info(f"[{channel_name}] Fluxo A: Whitelist com {len(known)} streamer(s). Coletando clipes cirurgicamente.")
        all_clips: List[Dict] = []

        async with httpx.AsyncClient(timeout=15) as client:
            token = await _get_twitch_token(client)

            for streamer in known:
                bid = streamer["broadcaster_id"]
                bname = streamer["broadcaster_name"]
                try:
                    clips = await fetch_top_clips(
                        client, token, bid,
                        target_type="channel",
                        hours_lookback=lookback_hours,
                        max_clips=50,  # Limite por streamer
                        min_views=min_views,
                    )
                    if clips:
                        # Filtrar apenas clips da categoria correta (game_id)
                        before = len(clips)
                        clips = [c for c in clips if c.get("game_id") == category_id]
                        if before != len(clips):
                            logger.info(f"  [{bname}] {before} clipe(s) brutos, {len(clips)} da categoria {channel_name}")
                        if clips:
                            logger.info(f"  [{bname}] {len(clips)} clipe(s) qualificado(s)")
                            all_clips.extend(clips)
                except Exception as e:
                    logger.warning(f"  [{bname}] Erro ao buscar clipes: {e}")
                    continue

                await asyncio.sleep(0.3)  # Respeitar rate limit entre streamers

        if not all_clips:
            _update_target_checked(target_id, found_clips=False)
            logger.info(f"[{channel_name}] Fluxo A: Nenhum clipe encontrado nos streamers mapeados.")
            return None

        # Dedup by both clip ID and URL + sort por views
        seen_ids = set()
        seen_urls = set()
        unique_clips = []
        for c in sorted(all_clips, key=lambda x: x.get("view_count", 0), reverse=True):
            if c["id"] not in seen_ids and c.get("url") not in seen_urls:
                seen_ids.add(c["id"])
                if c.get("url"):
                    seen_urls.add(c["url"])
                unique_clips.append(c)

        new_clips = _filter_already_processed(target_id, unique_clips)
        if not new_clips:
            _update_target_checked(target_id, found_clips=False)
            logger.info(f"[{channel_name}] Fluxo A: Clipes encontrados, mas todos ja processados.")
            return None

        job_ids = await _create_clip_jobs(target_id, channel_name, new_clips)
        return job_ids[0] if job_ids else None

    else:
        # ─── Fluxo B: Deep Pagination Fallback (Categoria Virgem) ───
        logger.info(f"[{channel_name}] Fluxo B: Whitelist vazia. Deep pagination por categoria.")

        async with httpx.AsyncClient(timeout=15) as client:
            token = await _get_twitch_token(client)
            clips = await fetch_top_clips(
                client, token, category_id,
                target_type="category",
                hours_lookback=lookback_hours,
                max_clips=max_clips,
                min_views=min_views,
            )

        if not clips:
            _update_target_checked(target_id, found_clips=False)
            logger.info(f"[{channel_name}] Fluxo B: Nenhum clipe PT-BR na categoria.")
            return None

        new_clips = _filter_already_processed(target_id, clips)
        if not new_clips:
            _update_target_checked(target_id, found_clips=False)
            logger.info(f"[{channel_name}] Fluxo B: Clipes encontrados, mas todos ja processados.")
            return None

        job_ids = await _create_clip_jobs(target_id, channel_name, new_clips)
        return job_ids[0] if job_ids else None


def _update_target_checked(target_id: int, found_clips: bool) -> None:
    """Atualiza o timestamp e contadores do target apos uma verificacao."""
    with safe_session() as db:
        t = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if t:
            t.last_checked_at = datetime.now(timezone.utc)
            if found_clips:
                t.last_clip_found_at = datetime.now(timezone.utc)
                t.consecutive_empty_checks = 0
            else:
                t.consecutive_empty_checks += 1
            db.commit()


MAX_JOB_RETRIES = 3  # Maximo de retries antes de desistir de um clip


def _filter_already_processed(target_id: int, clips: List[Dict]) -> List[Dict]:
    """
    Remove clipes que ja foram processados por jobs anteriores (dedup global).
    Inclui jobs 'failed' que ja esgotaram retries, evitando loop infinito.
    """
    with safe_session() as db:
        # Jobs ativos ou concluidos — nunca reprocessar
        active_urls = (
            db.query(ClipJob.clip_urls)
            .filter(ClipJob.status.in_(["pending", "downloading", "transcribing", "editing", "stitching", "completed", "waiting_clips"]))
            .order_by(ClipJob.id.desc())
            .limit(2000)
            .all()
        )
        already_processed = set()
        for (urls,) in active_urls:
            if urls:
                already_processed.update(urls)

        # Jobs falhados que ja esgotaram retries — nao reprocessar
        failed_maxed = (
            db.query(ClipJob.clip_urls)
            .filter(ClipJob.status == "failed")
            .filter(ClipJob.retry_count >= MAX_JOB_RETRIES)
            .order_by(ClipJob.id.desc())
            .limit(2000)
            .all()
        )
        for (urls,) in failed_maxed:
            if urls:
                already_processed.update(urls)

    return [c for c in clips if c["url"] not in already_processed]


# ─── Constantes de Chunking ──────────────────────────────────────────────
CHUNK_TARGET_DURATION = 90.0   # Duração alvo por postagem (1.5 minutos)
CHUNK_MIN_DURATION = 64.5      # Mínimo ~65s (crossfade consome ~2-3s, resultado final >= 61s). Uses 64.5 to handle floating point imprecision (e.g. 64.999s)
MAX_JOBS_PER_SCAN = 3          # Máximo de jobs criados por target por ciclo de scan
MAX_CLIPS_PER_JOB = 6          # Limite absoluto de clips por job (safety: evita jobs gigantes que enchem disco)
WAITING_JOB_TIMEOUT_HOURS = 72 # Timeout para jobs em waiting_clips


def _chunk_clips_by_duration(
    clips: List[Dict],
    target_duration: float = CHUNK_TARGET_DURATION,
    min_duration: float = CHUNK_MIN_DURATION,
) -> tuple[List[List[Dict]], List[Dict]]:
    """
    Agrupa clipes em chunks de ~target_duration segundos.
    Cada chunk se torna um ClipJob independente (= 1 postagem).

    Retorna:
        (ready_chunks, leftover_clips)
        - ready_chunks: chunks com >= min_duration (61s), prontos para processar
        - leftover_clips: clips que não atingiram 61s, irão para waiting_clips

    Regras:
    - Adiciona clips ao chunk atual até atingir target_duration
    - Chunks >= 61s são considerados prontos
    - Clips restantes < 61s ficam como leftover para jobs waiting_clips
    - Clips do mesmo game_id são priorizados juntos (coerência de conteúdo)
    """
    if not clips:
        return [], []

    chunks: List[List[Dict]] = []
    current_chunk: List[Dict] = []
    current_duration = 0.0

    for clip in clips:
        try:
            clip_dur = float(clip.get("duration") or 30)
        except (ValueError, TypeError):
            clip_dur = 30.0
        current_chunk.append(clip)
        current_duration += clip_dur

        if current_duration >= target_duration or len(current_chunk) >= MAX_CLIPS_PER_JOB:
            chunks.append(current_chunk)
            current_chunk = []
            current_duration = 0.0

    # Último chunk: se atingiu o mínimo de 61s, é um chunk válido
    if current_chunk:
        if current_duration >= min_duration:
            chunks.append(current_chunk)
        elif chunks:
            # Tentar anexar ao chunk anterior se couber razoavelmente
            prev_dur = sum(float(c.get("duration", 30)) for c in chunks[-1])
            if prev_dur + current_duration <= target_duration * 1.5:
                chunks[-1].extend(current_chunk)
            else:
                # Não cabe: leftover para waiting_clips
                return chunks, current_chunk
        else:
            # Único chunk e é < 61s: tudo vira leftover
            return [], current_chunk

    return chunks, []


MAX_QUEUE_JOBS = 10  # Limite de jobs ativos na esteira (evita encher disco)

async def _create_clip_jobs(target_id: int, channel_name: str, new_clips: List[Dict]) -> List[int]:
    """
    Agrupa clipes em chunks de ~90s (mín 61s) e cria um ClipJob por chunk.
    Clips que não atingem 61s são alimentados a jobs waiting_clips existentes
    ou criam um novo job waiting_clips.

    Cada job pronto resulta em 1 vídeo final = 1 postagem na fila de aprovação.
    """
    # ── Limite de esteira: não criar novos jobs se já atingiu o máximo ──
    with safe_session() as db:
        active_count = db.query(ClipJob).filter(
            ClipJob.status.in_(["pending", "downloading", "transcribing", "editing", "stitching", "waiting_clips"])
        ).count()
    if active_count >= MAX_QUEUE_JOBS:
        logger.warning(f"⛔ Esteira cheia: {active_count}/{MAX_QUEUE_JOBS} jobs ativos. Ignorando {len(new_clips)} clips novos.")
        return []

    # Dedup final: remover clips que já existem em qualquer waiting_clips job deste target
    with safe_session() as db:
        waiting_jobs = (
            db.query(ClipJob)
            .filter(ClipJob.target_id == target_id, ClipJob.status == "waiting_clips")
            .all()
        )
        existing_waiting_urls = set()
        for wj in waiting_jobs:
            existing_waiting_urls.update(wj.clip_urls or [])

    if existing_waiting_urls:
        before = len(new_clips)
        new_clips = [c for c in new_clips if c["url"] not in existing_waiting_urls]
        if len(new_clips) < before:
            logger.info(f"[{channel_name}] Dedup: {before - len(new_clips)} clip(s) já em waiting_clips, removidos")
        if not new_clips:
            logger.info(f"[{channel_name}] Todos os clips já estão em waiting_clips. Nada a fazer.")
            return []

    chunks, leftover = _chunk_clips_by_duration(new_clips)

    # 1. Tentar alimentar jobs waiting_clips existentes com leftover
    if leftover:
        leftover = await _feed_waiting_jobs(target_id, channel_name, leftover)

    # Cap: limitar quantidade de jobs criados por scan
    if len(chunks) > MAX_JOBS_PER_SCAN:
        logger.info(
            f"[{channel_name}] {len(chunks)} chunks disponíveis, limitando a {MAX_JOBS_PER_SCAN} (cap por scan)"
        )
        # Leftover dos chunks excedentes volta para waiting
        for extra_chunk in chunks[MAX_JOBS_PER_SCAN:]:
            leftover.extend(extra_chunk)
        chunks = chunks[:MAX_JOBS_PER_SCAN]

    job_ids: List[int] = []

    logger.info(
        f"[{channel_name}] {len(new_clips)} clipe(s) -> {len(chunks)} chunk(s) prontos"
        + (f", {len(leftover)} clip(s) em espera" if leftover else "")
    )

    # Buscar retry counts de jobs falhados anteriores para estes clips
    clip_retry_counts: Dict[str, int] = {}
    with safe_session() as db:
        failed_jobs = (
            db.query(ClipJob.clip_urls, ClipJob.retry_count)
            .filter(ClipJob.status == "failed")
            .filter(ClipJob.retry_count < MAX_JOB_RETRIES)
            .all()
        )
        for urls, count in failed_jobs:
            if urls:
                for u in urls:
                    clip_retry_counts[u] = max(clip_retry_counts.get(u, 0), (count or 0))

    from core.config import REDIS_HOST, REDIS_PORT
    try:
        pool = await create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
    except Exception as e:
        logger.error(f"[{channel_name}] Falha ao conectar ao Redis para enfileirar jobs: {e}", exc_info=True)
        return job_ids
    try:
        # 2. Criar jobs prontos (>= 61s)
        for i, chunk in enumerate(chunks):
            chunk_dur = sum(float(c.get("duration", 30)) for c in chunk)
            logger.info(
                f"  Chunk {i + 1}/{len(chunks)}: {len(chunk)} clip(s), ~{chunk_dur:.0f}s"
            )

            max_prev_retry = max((clip_retry_counts.get(c["url"], 0) for c in chunk), default=0)
            retry_count = max_prev_retry + 1

            with safe_session() as db:
                job = ClipJob(
                    target_id=target_id,
                    clip_urls=[c["url"] for c in chunk],
                    clip_metadata=chunk,
                    status="pending",
                    retry_count=retry_count,
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                job_id = job.id
                job_ids.append(job_id)

            try:
                await pool.enqueue_job("process_clip_job", job_id, _queue_name="clipper:queue")
                logger.info(f"✅ Job #{job_id} (Chunk {i + 1}, retry={retry_count}) enfileirado no Redis")
            except Exception as e:
                logger.error(f"❌ Falha ao enfileirar Job #{job_id}: {e}", exc_info=True)

        # 3. Criar job para leftover (se não foi absorvido)
        if leftover:
            leftover_dur = sum(float(c.get("duration", 30)) for c in leftover)

            if leftover_dur >= CHUNK_MIN_DURATION:
                # Leftover já atingiu 61s → criar como pending (pronto para processar)
                with safe_session() as db:
                    ready_job = ClipJob(
                        target_id=target_id,
                        clip_urls=[c["url"] for c in leftover],
                        clip_metadata=leftover,
                        status="pending",
                        current_step=f"Leftover pronto: {len(leftover)} clips, {leftover_dur:.0f}s",
                        progress_pct=0,
                    )
                    db.add(ready_job)
                    db.commit()
                    db.refresh(ready_job)
                    job_id = ready_job.id
                    job_ids.append(job_id)

                try:
                    await pool.enqueue_job("process_clip_job", job_id, _queue_name="clipper:queue")
                    logger.info(
                        f"✅ Job #{job_id} (leftover >= 61s) criado como pending: "
                        f"{len(leftover)} clip(s), {leftover_dur:.0f}s"
                    )
                except Exception as e:
                    logger.error(f"❌ Falha ao enfileirar Job #{job_id} (leftover): {e}")
            else:
                # Leftover < 61s → waiting_clips
                with safe_session() as db:
                    waiting_job = ClipJob(
                        target_id=target_id,
                        clip_urls=[c["url"] for c in leftover],
                        clip_metadata=leftover,
                        status="waiting_clips",
                        current_step=f"Aguardando mais clips ({leftover_dur:.0f}s / 61s mínimo)",
                        progress_pct=int(min(leftover_dur / 61.0 * 100, 99)),
                    )
                    db.add(waiting_job)
                    db.commit()
                    db.refresh(waiting_job)
                    logger.info(
                        f"⏳ Job #{waiting_job.id} criado em waiting_clips: "
                        f"{len(leftover)} clip(s), {leftover_dur:.0f}s (faltam {61 - leftover_dur:.0f}s)"
                    )
                    job_ids.append(waiting_job.id)

    finally:
        await pool.close()

    _update_target_checked(target_id, found_clips=True)

    with safe_session() as db:
        t = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if t:
            t.total_clips_processed += len(new_clips)
            db.commit()

    return job_ids


async def _feed_waiting_jobs(
    target_id: int, channel_name: str, new_clips: List[Dict]
) -> List[Dict]:
    """
    Alimenta jobs em waiting_clips com novos clips até atingirem 61s.
    Jobs que atingem 61s são promovidos para 'pending' e enfileirados.

    Retorna os clips que sobraram (não foram absorvidos por nenhum waiting job).
    """
    remaining = list(new_clips)

    with safe_session() as db:
        # Only feed waiting jobs that haven't expired (< 72h old)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=WAITING_JOB_TIMEOUT_HOURS)
        waiting_jobs = (
            db.query(ClipJob)
            .filter(
                ClipJob.target_id == target_id,
                ClipJob.status == "waiting_clips",
                ClipJob.created_at >= cutoff,
            )
            .order_by(ClipJob.created_at.asc())
            .all()
        )

        if not waiting_jobs:
            return remaining

        from core.config import REDIS_HOST, REDIS_PORT

        for job in waiting_jobs:
            if not remaining:
                break

            existing_urls = set(job.clip_urls or [])
            existing_dur = sum(
                float(c.get("duration", 30)) for c in (job.clip_metadata or [])
            )

            # Alimentar com novos clips até atingir 61s (respeitando limite por job)
            current_clip_count = len(job.clip_urls or [])
            added_clips = []
            for clip in list(remaining):
                if clip["url"] in existing_urls:
                    continue
                if current_clip_count + len(added_clips) >= MAX_CLIPS_PER_JOB:
                    break
                clip_dur = float(clip.get("duration", 30))
                added_clips.append(clip)
                existing_dur += clip_dur
                remaining.remove(clip)

                if existing_dur >= CHUNK_MIN_DURATION:
                    break

            if not added_clips:
                continue

            # Atualizar o job com os novos clips
            updated_urls = (job.clip_urls or []) + [c["url"] for c in added_clips]
            updated_meta = (job.clip_metadata or []) + added_clips
            job.clip_urls = updated_urls
            job.clip_metadata = updated_meta

            if existing_dur >= CHUNK_MIN_DURATION:
                # Promover para pending!
                job.status = "pending"
                job.current_step = f"Clips completos ({existing_dur:.0f}s). Pronto para processar!"
                job.progress_pct = 0
                db.commit()

                logger.info(
                    f"✅ Job #{job.id} promovido de waiting_clips → pending: "
                    f"{len(updated_urls)} clips, {existing_dur:.0f}s"
                )

                # Enfileirar no Redis (revert status if enqueue fails)
                try:
                    pool = await create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
                    try:
                        await pool.enqueue_job("process_clip_job", job.id, _queue_name="clipper:queue")
                    finally:
                        await pool.close()
                except Exception as e:
                    logger.error(f"Falha ao enfileirar Job #{job.id} promovido, revertendo para waiting_clips: {e}")
                    with safe_session() as db2:
                        reverted = db2.query(ClipJob).filter(ClipJob.id == job.id).first()
                        if reverted and reverted.status == "pending":
                            reverted.status = "waiting_clips"
                            reverted.current_step = f"Aguardando retry enqueue ({existing_dur:.0f}s / 61s mínimo)"
                            db2.commit()
            else:
                job.current_step = f"Aguardando mais clips ({existing_dur:.0f}s / 61s mínimo)"
                job.progress_pct = int(min(existing_dur / 61.0 * 100, 99))
                db.commit()
                logger.info(
                    f"⏳ Job #{job.id} alimentado: +{len(added_clips)} clips, "
                    f"agora {existing_dur:.0f}s (faltam {61 - existing_dur:.0f}s)"
                )

    return remaining


async def _consolidate_waiting_jobs() -> None:
    """
    Consolida múltiplos jobs waiting_clips do mesmo target em um único job.
    Se o job consolidado atingir 61s, promove automaticamente para pending.

    Chamado no início de cada ciclo de scan, ANTES de verificar expiração.
    """
    from sqlalchemy import func

    with safe_session() as db:
        # Encontrar targets com mais de 1 job waiting_clips
        duplicates = (
            db.query(ClipJob.target_id, func.count(ClipJob.id).label("cnt"))
            .filter(ClipJob.status == "waiting_clips")
            .group_by(ClipJob.target_id)
            .having(func.count(ClipJob.id) > 1)
            .all()
        )

        if not duplicates:
            return

        from core.config import REDIS_HOST, REDIS_PORT
        promoted_ids = []

        for target_id, count in duplicates:
            # Buscar todos os waiting jobs deste target, ordenados por criação
            jobs = (
                db.query(ClipJob)
                .filter(ClipJob.target_id == target_id, ClipJob.status == "waiting_clips")
                .order_by(ClipJob.created_at.asc())
                .all()
            )

            if len(jobs) <= 1:
                continue

            # O primeiro job (mais antigo) absorve todos os outros
            primary = jobs[0]
            merged_urls = list(primary.clip_urls or [])
            merged_meta = list(primary.clip_metadata or [])
            absorbed_ids = []

            for donor in jobs[1:]:
                donor_urls = donor.clip_urls or []
                donor_meta = donor.clip_metadata or []

                for url, meta in zip(donor_urls, donor_meta):
                    if url not in merged_urls:
                        merged_urls.append(url)
                        merged_meta.append(meta)

                absorbed_ids.append(donor.id)
                db.delete(donor)

            primary.clip_urls = merged_urls
            primary.clip_metadata = merged_meta

            total_dur = sum(float(c.get("duration", 30)) for c in merged_meta)

            if total_dur >= CHUNK_MIN_DURATION:
                # Consolidação atingiu 61s → promover!
                primary.status = "pending"
                primary.current_step = f"Consolidado: {len(merged_urls)} clips, {total_dur:.0f}s. Pronto!"
                primary.progress_pct = 0
                promoted_ids.append(primary.id)
                logger.info(
                    f"🔗 Job #{primary.id} consolidado e promovido → pending: "
                    f"{len(merged_urls)} clips de {count} jobs, {total_dur:.0f}s "
                    f"(absorveu jobs {absorbed_ids})"
                )
            else:
                primary.current_step = f"Consolidado: {total_dur:.0f}s / 61s mínimo ({len(merged_urls)} clips)"
                primary.progress_pct = int(min(total_dur / 61.0 * 100, 99))
                logger.info(
                    f"🔗 Job #{primary.id} consolidado: {len(merged_urls)} clips de {count} jobs, "
                    f"{total_dur:.0f}s (absorveu jobs {absorbed_ids}, faltam {61 - total_dur:.0f}s)"
                )

        db.commit()

        # Enfileirar jobs promovidos
        if promoted_ids:
            try:
                pool = await create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
                try:
                    for job_id in promoted_ids:
                        await pool.enqueue_job("process_clip_job", job_id, _queue_name="clipper:queue")
                    logger.info(f"🔗 {len(promoted_ids)} job(s) consolidados enfileirados para processamento")
                finally:
                    await pool.close()
            except Exception as e:
                logger.error(f"Falha ao enfileirar jobs consolidados: {e}")


async def _promote_expired_waiting_jobs() -> None:
    """
    Promove jobs waiting_clips que expiraram o timeout (72h) para pending.
    Esses jobs serão processados com loop-tail como fallback.
    Chamado no início de cada ciclo de scan.
    """
    with safe_session() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=WAITING_JOB_TIMEOUT_HOURS)
        expired = (
            db.query(ClipJob)
            .filter(
                ClipJob.status == "waiting_clips",
                ClipJob.created_at < cutoff,
            )
            .all()
        )

        if not expired:
            return

        from core.config import REDIS_HOST, REDIS_PORT

        for job in expired:
            total_dur = sum(float(c.get("duration", 30)) for c in (job.clip_metadata or []))
            job.status = "pending"
            job.current_step = f"Timeout 72h atingido ({total_dur:.0f}s). Processando com loop."
            job.progress_pct = 0
            logger.warning(
                f"⏰ Job #{job.id} expirou waiting_clips após 72h: "
                f"{len(job.clip_urls or [])} clips, {total_dur:.0f}s. Forçando processamento."
            )

        db.commit()

        # Enfileirar todos
        try:
            pool = await create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
            try:
                for job in expired:
                    await pool.enqueue_job("process_clip_job", job.id, _queue_name="clipper:queue")
            finally:
                await pool.close()
        except Exception as e:
            logger.error(f"Falha ao enfileirar jobs expirados: {e}")


async def monitor_loop(interval_seconds: int = 60):
    """
    Loop principal do monitoramento. Roda indefinidamente checando
    targets ativos respeitando o check_interval_minutes de cada um.

    Default poll: 60s (verifica quem esta pronto a cada 1 min).
    """
    logger.info(f"Clipper Monitor iniciado. Poll interval: {interval_seconds}s")

    while True:
        try:
            await _check_all_targets()
        except Exception as e:
            logger.error(f"Erro no monitor loop: {e}", exc_info=True)

        await asyncio.sleep(interval_seconds)


def _get_ready_target_ids() -> List[int]:
    """Sincrono: Fetches ready targets from DB para rodar fora do event loop."""
    now = datetime.now(timezone.utc)
    with safe_session() as db:
        targets = (
            db.query(TwitchTarget)
            .filter(TwitchTarget.active.is_(True))
            .all()
        )
        ready_targets = []
        for t in targets:
            interval_minutes = t.check_interval_minutes or 15
            if t.last_checked_at is None:
                ready_targets.append(t.id)
            else:
                last = t.last_checked_at
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                if (now - last).total_seconds() >= interval_minutes * 60:
                    ready_targets.append(t.id)
        return ready_targets

async def _check_all_targets() -> None:
    """Verifica targets ativos cujo intervalo de check ja expirou."""
    # 1. Consolidar waiting_clips duplicados do mesmo target
    try:
        await _consolidate_waiting_jobs()
    except Exception as e:
        logger.error(f"Erro ao consolidar waiting jobs: {e}", exc_info=True)

    # 2. Promover jobs waiting_clips que expiraram o timeout de 72h
    try:
        await _promote_expired_waiting_jobs()
    except Exception as e:
        logger.error(f"Erro ao promover waiting jobs expirados: {e}", exc_info=True)

    # Roda DB call bloqueante em thread separada
    ready_targets = await asyncio.to_thread(_get_ready_target_ids)

    if not ready_targets:
        return

    logger.info(f"Verificando {len(ready_targets)} target(s) prontos para check...")
    for tid in ready_targets:
        try:
            job_id = await check_target(tid)
            if job_id:
                logger.info(f"ClipJob(s) criado(s) a partir do target {tid}.")
        except Exception as e:
            logger.error(f"Erro ao verificar target {tid}: {e}", exc_info=True)
        # Pequeno delay entre targets para nao bater rate limit
        await asyncio.sleep(2)

