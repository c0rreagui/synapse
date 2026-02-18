
import asyncio
import os
import sys
# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.circuit_breaker import circuit_breaker, CIRCUIT_BREAKER_THRESHOLD

async def test_circuit_breaker():
    print("Testing Circuit Breaker...")
    
    # 1. Reset state
    await circuit_breaker.reset()
    assert circuit_breaker.state == "CLOSED"
    assert circuit_breaker.is_open() == False
    print("Initial State: CLOSED")

    # 2. Record Failures up to Threshold
    print(f"Recording {CIRCUIT_BREAKER_THRESHOLD} failures...")
    for i in range(CIRCUIT_BREAKER_THRESHOLD):
        await circuit_breaker.record_failure()
        print(f"   - Failure {i+1} recorded. Count: {circuit_breaker.failure_count}")

    # 3. Verify Open
    assert circuit_breaker.state == "OPEN"
    assert circuit_breaker.is_open() == True
    print("Circuit Breaker TRIPPED (OPEN) as expected.")

    # 4. Verify Persistence (Reload)
    print("Testing Persistence...")
    # Simulate restart by creating new instance (singleton logic might prevent new obj, but we re-call load_state)
    circuit_breaker.load_state() 
    assert circuit_breaker.state == "OPEN"
    print("State persisted/loaded correctly.")

    # 5. Reset
    await circuit_breaker.reset()
    assert circuit_breaker.state == "CLOSED"
    print("Reset successful.")

    print("All Circuit Breaker tests passed!")

if __name__ == "__main__":
    asyncio.run(test_circuit_breaker())
