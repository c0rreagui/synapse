import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from core.circuit_breaker import circuit_breaker

async def main():
    print(f"Current Circuit Breaker State: {'OPEN' if circuit_breaker.is_open() else 'CLOSED'}")
    print(f"Failure Count: {circuit_breaker.failure_count}")
    
    if circuit_breaker.is_open():
        print("\nResetting Circuit Breaker...")
        await circuit_breaker.reset()
        print(f"New State: {'OPEN' if circuit_breaker.is_open() else 'CLOSED'}")
        print("Circuit Breaker RESET successfully.")
    else:
        print("\nCircuit Breaker is already CLOSED. No action needed.")

if __name__ == "__main__":
    asyncio.run(main())
