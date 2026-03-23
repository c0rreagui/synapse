"""
Clipper Scheduler — Frequência Inteligente & Rate Limits (SYN-128)
==================================================================

Orquestra a execução do monitor.py com:
- Micro-lookbacks (janelas de 6h ao invés de 24h)
- Sharding temporal (distribui targets em minutos distintos)
- Monitoramento de rate limit via cabeçalhos Twitch (Ratelimit-Remaining)

Este módulo substitui o monitor_loop simples por uma lógica consciente
de limites de API e distribuição temporal.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from core.database import safe_session
from core.clipper.models import TwitchTarget
from core.clipper.monitor import check_target

logger = logging.getLogger("ClipperScheduler")

SP_TZ = ZoneInfo("America/Sao_Paulo")


# ─── Rate Limit State (Global) ──────────────────────────────────────────

class RateLimitState:
    """
    Rastreia o estado do rate limit da Twitch API.
    Atualizado a cada resposta HTTP via update_from_headers().
    """
    def __init__(self):
        self.remaining: int = 800  # Twitch padrão = 800 req / 60s
        self.limit: int = 800
        self.reset_at: float = 0.0  # Unix timestamp
        self._last_updated: float = 0.0

    def update_from_headers(self, headers: dict) -> None:
        """Extrai Ratelimit-Remaining e Ratelimit-Reset dos headers HTTP."""
        try:
            remaining = headers.get("ratelimit-remaining") or headers.get("Ratelimit-Remaining")
            limit = headers.get("ratelimit-limit") or headers.get("Ratelimit-Limit")
            reset_at = headers.get("ratelimit-reset") or headers.get("Ratelimit-Reset")

            if remaining is not None:
                self.remaining = int(remaining)
            if limit is not None:
                self.limit = int(limit)
            if reset_at is not None:
                self.reset_at = float(reset_at)
            self._last_updated = time.time()
        except (ValueError, TypeError) as e:
            logger.warning(f"Erro ao parsear headers de rate limit: {e}")

    @property
    def is_critical(self) -> bool:
        """Retorna True se estamos abaixo de 10% do limite."""
        return self.remaining < (self.limit * 0.10)

    @property
    def is_warning(self) -> bool:
        """Retorna True se estamos abaixo de 25% do limite."""
        return self.remaining < (self.limit * 0.25)

    @property
    def seconds_until_reset(self) -> float:
        """Segundos até o reset do rate limit."""
        if self.reset_at <= 0:
            return 0
        return max(0, self.reset_at - time.time())

    def __repr__(self) -> str:
        return f"RateLimit({self.remaining}/{self.limit}, reset_in={self.seconds_until_reset:.0f}s)"


# Instância global
rate_limit = RateLimitState()


# ─── Sharding Temporal ──────────────────────────────────────────────────

def _get_shard_delay(target_id: int, total_targets: int, interval_minutes: int = 15) -> int:
    """
    Calcula o delay (em segundos) para um target baseado em sharding temporal.
    Distribui os targets uniformemente dentro do intervalo de check.

    Ex: 4 targets com intervalo de 15min:
      - Target 0: delay 0s   (minuto 00)
      - Target 1: delay 225s (minuto ~04)
      - Target 2: delay 450s (minuto ~07)
      - Target 3: delay 675s (minuto ~11)
    """
    if total_targets <= 1:
        return 0

    slot_size_seconds = (interval_minutes * 60) // total_targets
    shard_index = target_id % total_targets
    return shard_index * slot_size_seconds


# ─── Scheduler Loop ─────────────────────────────────────────────────────

async def clipper_scheduler_loop(poll_interval: int = 60):
    """
    Loop principal do Clipper Scheduler (SYN-128).
    Substitui o monitor_loop simples com:
    - Sharding temporal entre targets
    - Monitoramento de rate limit
    - Backoff adaptativo quando próximo do limite
    - Garbage collector periódico (a cada 1h)
    """
    logger.info(f"Clipper Scheduler iniciado (SYN-128). Poll: {poll_interval}s")

    gc_interval = 1 * 3600  # 1 hora
    last_gc = 0.0

    while True:
        try:
            await _scheduled_check_cycle()
        except Exception as e:
            logger.error(f"Erro no clipper scheduler: {e}", exc_info=True)

        # Garbage Collector periódico (a cada 6h)
        now = time.time()
        if now - last_gc > gc_interval:
            try:
                from core.clipper.garbage_collector import run_gc
                await asyncio.to_thread(run_gc)
                last_gc = now
            except Exception as e:
                logger.error(f"Erro no Garbage Collector: {e}", exc_info=True)

        await asyncio.sleep(poll_interval)


async def _scheduled_check_cycle() -> None:
    """
    Um ciclo completo do scheduler:
    1. Busca targets prontos para check
    2. Aplica sharding temporal (delay entre targets)
    3. Monitora rate limit e aplica backoff se necessário
    """
    try:
        ready_targets = await asyncio.wait_for(
            asyncio.to_thread(_get_ready_target_ids_with_priority), timeout=30
        )
    except asyncio.TimeoutError:
        logger.warning("Scheduler: DB query timeout (30s) ao buscar targets prontos.")
        return

    if not ready_targets:
        return

    total = len(ready_targets)
    logger.info(f"Scheduler: {total} target(s) prontos. Rate limit: {rate_limit}")

    for i, (tid, target_type) in enumerate(ready_targets):
        # Rate limit check: pausar se crítico
        if rate_limit.is_critical:
            wait_time = rate_limit.seconds_until_reset + 5  # +5s margem
            logger.warning(
                f"⚠️ Rate limit CRÍTICO ({rate_limit.remaining}/{rate_limit.limit}). "
                f"Pausando por {wait_time:.0f}s até reset."
            )
            await asyncio.sleep(wait_time)

        # Rate limit warning: delay extra
        elif rate_limit.is_warning:
            logger.info(f"⚡ Rate limit warning ({rate_limit.remaining}/{rate_limit.limit}). Delay extra 3s.")
            await asyncio.sleep(3)

        try:
            await check_target(tid)
        except Exception as e:
            logger.error(f"Erro ao verificar target {tid}: {e}", exc_info=True)

        # Sharding: delay entre targets para distribuir carga
        base_delay = 2  # Mínimo 2s entre targets
        shard_delay = _get_shard_delay(i, total)
        extra_delay = min(shard_delay, 10)  # Cap em 10s extra
        await asyncio.sleep(base_delay + extra_delay)


def _get_ready_target_ids_with_priority() -> list[tuple[int, str]]:
    """
    Busca targets prontos para check, ordenados por prioridade:
    1. Categorias (precisam do radar + whitelist, mais custoso)
    2. Canais diretos (mais rápidos)

    Retorna lista de (target_id, target_type).
    """
    now = datetime.now(timezone.utc)
    with safe_session() as db:
        targets = (
            db.query(TwitchTarget)
            .filter(TwitchTarget.active.is_(True))
            .all()
        )
        ready: list[tuple[int, str]] = []
        for t in targets:
            interval_minutes = t.check_interval_minutes or 15
            if t.last_checked_at is None:
                ready.append((t.id, t.target_type))
            else:
                # Normalizar timezone: DB pode retornar naive datetime
                last = t.last_checked_at
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                if (now - last).total_seconds() >= interval_minutes * 60:
                    ready.append((t.id, t.target_type))

        # Canais primeiro (mais rápidos), depois categorias
        ready.sort(key=lambda x: 0 if x[1] != "category" else 1)
        return ready
