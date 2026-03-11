"""
Radar de Lives PT-BR — Descoberta Ativa de Streamers Brasileiros (SYN-126)
==========================================================================

Consulta a API /streams da Twitch filtrando por `language=pt` e `game_id`
para mapear streamers online e alimentar a tabela `TwitchKnownStreamer`.
Essa whitelist é usada pelo monitor.py (SYN-127) para coleta cirúrgica.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import httpx

from core.database import safe_session
from core.clipper.models import TwitchKnownStreamer
from core.clipper.monitor import _get_twitch_token, TWITCH_HELIX_URL
from core.config import TWITCH_CLIENT_ID

logger = logging.getLogger("ClipperRadar")


async def fetch_live_br_streams(
    client: httpx.AsyncClient,
    token: str,
    game_id: str,
    max_pages: int = 3,
) -> List[Dict[str, Any]]:
    """
    Busca streams ao vivo em PT-BR para um game_id específico.
    Itera até `max_pages` páginas (cada uma com até 100 resultados).

    Retorna lista de dicts com broadcaster_id, broadcaster_name, language.
    """
    all_streams: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    for page in range(max_pages):
        params: Dict[str, Any] = {
            "game_id": game_id,
            "language": "pt",
            "first": 100,
        }
        if cursor:
            params["after"] = cursor

        try:
            resp = await client.get(
                f"{TWITCH_HELIX_URL}/streams",
                params=params,
                headers={
                    "Client-Id": TWITCH_CLIENT_ID,
                    "Authorization": f"Bearer {token}",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            logger.warning(f"Erro HTTP ao buscar streams PT-BR (pag {page + 1}): {e}")
            break

        streams = data.get("data", [])
        all_streams.extend(streams)

        cursor = data.get("pagination", {}).get("cursor")
        if not cursor:
            break

    logger.info(
        f"Radar: {len(all_streams)} stream(s) PT-BR encontrada(s) para game_id={game_id}"
    )
    return all_streams


def _upsert_known_streamers(
    streams: List[Dict[str, Any]],
    category_id: str,
) -> int:
    """
    Insere ou atualiza streamers na tabela TwitchKnownStreamer.
    Usa broadcaster_id + category_id como chave única (upsert).
    Retorna o número de novos streamers inseridos.
    """
    new_count = 0

    with safe_session() as db:
        for stream in streams:
            broadcaster_id = stream.get("user_id")
            broadcaster_name = stream.get("user_name") or stream.get("user_login", "")
            language = stream.get("language", "pt")

            if not broadcaster_id:
                continue

            existing = (
                db.query(TwitchKnownStreamer)
                .filter(
                    TwitchKnownStreamer.broadcaster_id == broadcaster_id,
                    TwitchKnownStreamer.category_id == category_id,
                )
                .first()
            )

            if existing:
                # Atualiza last_seen_live
                existing.last_seen_live = datetime.now(timezone.utc)
                existing.broadcaster_name = broadcaster_name
            else:
                # Novo streamer descoberto
                new_streamer = TwitchKnownStreamer(
                    broadcaster_id=broadcaster_id,
                    broadcaster_name=broadcaster_name,
                    category_id=category_id,
                    language=language,
                    last_seen_live=datetime.now(timezone.utc),
                )
                db.add(new_streamer)
                new_count += 1

        db.commit()

    if new_count > 0:
        logger.info(f"Radar: {new_count} novo(s) streamer(s) adicionado(s) à whitelist (category={category_id})")

    return new_count


async def scan_category(category_id: str) -> int:
    """
    Executa o fluxo completo do radar para uma categoria:
    1. Busca streams PT-BR ao vivo
    2. Salva/atualiza na whitelist

    Retorna o número de novos streamers descobertos.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        token = await _get_twitch_token(client)
        streams = await fetch_live_br_streams(client, token, category_id)

    if not streams:
        logger.info(f"Radar: Nenhuma stream PT-BR ao vivo para category_id={category_id}")
        return 0

    return _upsert_known_streamers(streams, category_id)


def get_known_streamers(category_id: str) -> List[Dict[str, str]]:
    """
    Retorna a lista de streamers conhecidos para uma categoria.
    Ordenado por último visto live (mais recente primeiro).
    """
    with safe_session() as db:
        streamers = (
            db.query(TwitchKnownStreamer)
            .filter(TwitchKnownStreamer.category_id == category_id)
            .order_by(TwitchKnownStreamer.last_seen_live.desc().nulls_last())
            .all()
        )
        return [
            {
                "broadcaster_id": s.broadcaster_id,
                "broadcaster_name": s.broadcaster_name,
                "language": s.language,
                "clip_count": s.clip_count,
            }
            for s in streamers
        ]
