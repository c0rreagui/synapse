import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.circuit_breaker import circuit_breaker

import asyncio

async def reset_cb():
    # Force close via direct redis/method call if possible, otherwise rely on reset()
    # Assuming reset() is async based on error
    print(f"Estado Atual (Pre-Reset): {'ABERTO' if circuit_breaker.is_open() else 'FECHADO'}")
    await circuit_breaker.reset()
    print(f"Novo Estado (Pos-Reset): {'ABERTO' if circuit_breaker.is_open() else 'FECHADO'}")

if __name__ == "__main__":
    asyncio.run(reset_cb())
