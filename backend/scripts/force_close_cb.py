import script_env
script_env.setup_script_env()
import asyncio
from core.circuit_breaker import CircuitBreaker

async def reset():
    print("[RESET] Forcing Circuit Breaker CLOSE...")
    cb = CircuitBreaker()
    # Force state
    cb.state = "CLOSED"
    cb.failure_count = 0
    cb.save_state() # Sync method
    print("[RESET] Circuit Breaker is now CLOSED.")

if __name__ == "__main__":
    asyncio.run(reset())
