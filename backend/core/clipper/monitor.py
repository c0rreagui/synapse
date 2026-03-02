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

from core.database import safe_session
from core.clipper.models import TwitchTarget, ClipJob

logger = logging.getLogger("ClipperMonitor")

SP_TZ = ZoneInfo("America/Sao_Paulo")

# ─── Twitch OAuth2 ──────────────────────────────────────────────────────

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
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

    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
        raise RuntimeError(
            "TWITCH_CLIENT_ID e TWITCH_CLIENT_SECRET devem estar configurados no .env"
        )

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

def _extract_channel_name(url: str) -> str:
    """
    Extrai o nome do canal de uma URL da Twitch.
    Aceita formatos:
        https://www.twitch.tv/gaules
        https://twitch.tv/gaules
        twitch.tv/gaules
        gaules (nome direto)
    """
    url = url.strip().rstrip("/")
    if "/" in url:
        return url.split("/")[-1].lower()
    return url.lower()


async def _resolve_broadcaster_id(
    client: httpx.AsyncClient, token: str, channel_name: str
) -> Optional[str]:
    """Resolve o nome do canal para broadcaster_id via Twitch Helix API."""
    resp = await client.get(
        f"{TWITCH_HELIX_URL}/users",
        params={"login": channel_name},
        headers={
            "Client-Id": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    users = data.get("data", [])
    if not users:
        logger.warning(f"Canal '{channel_name}' nao encontrado na Twitch.")
        return None

    return users[0]["id"]


# ─── Busca de Clipes ────────────────────────────────────────────────────

async def fetch_top_clips(
    client: httpx.AsyncClient,
    token: str,
    broadcaster_id: str,
    hours_lookback: int = 24,
    max_clips: int = 5,
    min_views: int = 100,
) -> List[Dict[str, Any]]:
    """
    Busca os Top Clips de um broadcaster nas ultimas N horas.

    Returns:
        Lista de dicts com: id, url, title, view_count, duration, creator_name, created_at
    """
    now = datetime.now(timezone.utc)
    started_at = (now - timedelta(hours=hours_lookback)).isoformat()
    ended_at = now.isoformat()

    resp = await client.get(
        f"{TWITCH_HELIX_URL}/clips",
        params={
            "broadcaster_id": broadcaster_id,
            "first": max_clips * 2,  # Pega extras para filtrar por views
            "started_at": started_at,
            "ended_at": ended_at,
        },
        headers={
            "Client-Id": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    clips = data.get("data", [])

    # Filtrar por minimo de views e ordenar por view_count desc
    filtered = [c for c in clips if c.get("view_count", 0) >= min_views]
    filtered.sort(key=lambda c: c.get("view_count", 0), reverse=True)

    results = []
    for clip in filtered[:max_clips]:
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
        })

    return results


# ─── Registro de Alvos ──────────────────────────────────────────────────

async def register_target(channel_url: str) -> Dict[str, Any]:
    """
    Cadastra um novo canal da Twitch para monitoramento.
    Resolve automaticamente o broadcaster_id.

    Returns:
        Dict com dados do TwitchTarget criado.
    """
    channel_name = _extract_channel_name(channel_url)

    async with httpx.AsyncClient(timeout=15) as client:
        token = await _get_twitch_token(client)
        broadcaster_id = await _resolve_broadcaster_id(client, token, channel_name)

    if not broadcaster_id:
        raise ValueError(f"Canal '{channel_name}' nao encontrado na Twitch API.")

    with safe_session() as db:
        # Verifica duplicata
        existing = db.query(TwitchTarget).filter(
            TwitchTarget.channel_name == channel_name
        ).first()

        if existing:
            # Reativar se desativado
            if not existing.active:
                existing.active = True
                existing.broadcaster_id = broadcaster_id
                db.commit()
                logger.info(f"Canal '{channel_name}' reativado.")
            return {
                "id": existing.id,
                "channel_name": existing.channel_name,
                "broadcaster_id": existing.broadcaster_id,
                "status": "already_registered",
            }

        target = TwitchTarget(
            channel_url=channel_url.strip(),
            channel_name=channel_name,
            broadcaster_id=broadcaster_id,
        )
        db.add(target)
        db.commit()
        db.refresh(target)

        logger.info(f"Canal '{channel_name}' (ID: {broadcaster_id}) cadastrado para monitoramento.")
        return {
            "id": target.id,
            "channel_name": target.channel_name,
            "broadcaster_id": target.broadcaster_id,
            "status": "created",
        }


# ─── Loop Principal do CronJob ──────────────────────────────────────────

async def check_target(target_id: int) -> Optional[int]:
    """
    Verifica um unico TwitchTarget por novos clipes.
    Se encontrar, cria um ClipJob e retorna seu ID.
    """
    with safe_session() as db:
        target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if not target or not target.active:
            return None

        broadcaster_id = target.broadcaster_id
        channel_name = target.channel_name
        max_clips = target.max_clips_per_check
        min_views = target.min_clip_views

    if not broadcaster_id:
        logger.warning(f"Target {target_id} ({channel_name}) sem broadcaster_id. Pulando.")
        return None

    async with httpx.AsyncClient(timeout=15) as client:
        token = await _get_twitch_token(client)
        clips = await fetch_top_clips(
            client, token, broadcaster_id,
            hours_lookback=24,
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

    return _create_clip_job(target_id, channel_name, new_clips)


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


def _filter_already_processed(target_id: int, clips: List[Dict]) -> List[Dict]:
    """Remove clipes que ja foram processados por jobs anteriores."""
    with safe_session() as db:
        existing_jobs = (
            db.query(ClipJob)
            .filter(ClipJob.target_id == target_id)
            .filter(ClipJob.status.in_(["pending", "downloading", "transcribing", "editing", "stitching", "completed"]))
            .all()
        )
        already_processed = set()
        for job in existing_jobs:
            if job.clip_urls:
                already_processed.update(job.clip_urls)

    return [c for c in clips if c["url"] not in already_processed]


def _create_clip_job(target_id: int, channel_name: str, new_clips: List[Dict]) -> int:
    """Cria um ClipJob com os melhores clipes novos e atualiza o target."""
    selected = new_clips[:2] if len(new_clips) >= 2 else new_clips

    with safe_session() as db:
        job = ClipJob(
            target_id=target_id,
            clip_urls=[c["url"] for c in selected],
            clip_metadata=selected,
            status="pending",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

    _update_target_checked(target_id, found_clips=True)

    with safe_session() as db:
        t = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
        if t:
            t.total_clips_processed += len(selected)
            db.commit()

    logger.info(
        f"[{channel_name}] {len(selected)} clipe(s) novo(s) encontrado(s). "
        f"ClipJob #{job_id} criado."
    )
    return job_id


async def monitor_loop(interval_seconds: int = 900):
    """
    Loop principal do monitoramento. Roda indefinidamente checando
    todos os targets ativos a cada `interval_seconds`.

    Default: 900s = 15 minutos.
    """
    logger.info(f"Clipper Monitor iniciado. Intervalo: {interval_seconds}s")

    while True:
        try:
            await _check_all_targets()
        except Exception as e:
            logger.error(f"Erro no monitor loop: {e}", exc_info=True)

        await asyncio.sleep(interval_seconds)


async def _check_all_targets() -> None:
    """Verifica todos os targets ativos por novos clipes."""
    with safe_session() as db:
        targets = (
            db.query(TwitchTarget)
            .filter(TwitchTarget.active.is_(True))
            .all()
        )
        target_ids = [t.id for t in targets]

    if not target_ids:
        logger.debug("Nenhum target ativo. Aguardando...")
        return

    logger.info(f"Verificando {len(target_ids)} target(s) ativo(s)...")
    for tid in target_ids:
        try:
            job_id = await check_target(tid)
            if job_id:
                logger.info(f"ClipJob #{job_id} enfileirado para processamento.")
        except Exception as e:
            logger.error(f"Erro ao verificar target {tid}: {e}", exc_info=True)
        # Pequeno delay entre targets para nao bater rate limit
        await asyncio.sleep(2)

