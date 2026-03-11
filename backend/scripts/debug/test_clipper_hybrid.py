"""
Test Clipper Hybrid — Script de Teste da Arquitetura Híbrida (SYN-125)
======================================================================

Testa os fluxos do monitor.py (Fluxo A + B) e do radar.py
para uma categoria específica.

Uso:
    cd backend/
    python scripts/debug/test_clipper_hybrid.py
"""

import os
import sys
import asyncio
import logging

# Adiciona backend/ ao sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("TestClipperHybrid")


async def test_radar(category_id: str):
    """Testa o radar de lives PT-BR."""
    from core.clipper.radar import scan_category, get_known_streamers

    logger.info("=" * 60)
    logger.info(f"[RADAR] Testando scan_category('{category_id}')")
    logger.info("=" * 60)

    new_count = await scan_category(category_id)
    logger.info(f"Novos streamers descobertos: {new_count}")

    known = get_known_streamers(category_id)
    logger.info(f"Total na whitelist: {len(known)}")
    for s in known[:10]:  # Mostra até 10
        logger.info(f"  • {s['broadcaster_name']} (ID: {s['broadcaster_id']}, clips: {s['clip_count']})")

    return known


async def test_check_target(target_id: int):
    """Testa o check_target com a arquitetura híbrida."""
    from core.clipper.monitor import check_target

    logger.info("=" * 60)
    logger.info(f"[MONITOR] Testando check_target(target_id={target_id})")
    logger.info("=" * 60)

    job_id = await check_target(target_id)
    if job_id:
        logger.info(f"✅ ClipJob criado! ID: {job_id}")
    else:
        logger.info("ℹ️ Nenhum ClipJob criado (sem clipes novos ou duplicados).")

    return job_id


async def test_rate_limit_state():
    """Exibe o estado atual do rate limit."""
    try:
        from core.clipper.scheduler import rate_limit
        logger.info("=" * 60)
        logger.info("[RATE LIMIT] Estado atual")
        logger.info("=" * 60)
        logger.info(f"  Remaining: {rate_limit.remaining}/{rate_limit.limit}")
        logger.info(f"  Critical:  {rate_limit.is_critical}")
        logger.info(f"  Warning:   {rate_limit.is_warning}")
        logger.info(f"  Reset in:  {rate_limit.seconds_until_reset:.0f}s")
    except ImportError:
        logger.warning("scheduler.py não disponível (rate limit state não inicializado)")


async def test_whitelist_db():
    """Testa operações CRUD na tabela TwitchKnownStreamer."""
    from core.database import safe_session
    from core.clipper.models import TwitchKnownStreamer

    logger.info("=" * 60)
    logger.info("[DB] Testando TwitchKnownStreamer")
    logger.info("=" * 60)

    with safe_session() as db:
        total = db.query(TwitchKnownStreamer).count()
        logger.info(f"Total de streamers na whitelist: {total}")

        # Listar por categoria
        from sqlalchemy import func
        by_cat = (
            db.query(
                TwitchKnownStreamer.category_id,
                func.count(TwitchKnownStreamer.id),
            )
            .group_by(TwitchKnownStreamer.category_id)
            .all()
        )
        for cat_id, count in by_cat:
            logger.info(f"  Categoria {cat_id}: {count} streamer(s)")


async def main():
    """Executa todos os testes sequencialmente."""
    logger.info("🚀 Iniciando testes da Arquitetura Híbrida (SYN-125)")
    logger.info("")

    # 1. Testar DB
    await test_whitelist_db()

    # 2. Testar radar com Just Chatting (category_id = 509658)
    #    Para testar com outra categoria, altere o ID abaixo.
    CATEGORY_ID = "509658"  # Just Chatting
    await test_radar(CATEGORY_ID)

    # 3. Testar rate limit
    await test_rate_limit_state()

    # 4. (Opcional) Testar check_target
    #    Descomente e ajuste o target_id para um alvo "category" existente no banco.
    # await test_check_target(target_id=1)

    logger.info("")
    logger.info("✅ Todos os testes concluídos!")


if __name__ == "__main__":
    asyncio.run(main())
