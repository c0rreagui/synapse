import asyncio
import sys
import os
import io

# Fix Windows Console Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.scheduler import Scheduler

async def main():
    print("Triggering manual retry for item 31...")
    try:
        # Create a fresh instance since we are in a script, 
        # but be careful about the database session if it's singleton.
        # Scheduler() usually inits fine.
        s = Scheduler()
        
        # Ensure we pass the ID as an integer or string depending on DB? 
        # Models usually Use Integer, but Scheduler.retry_event type hint said str.
        # Let's try Integer first as it is in DB.
        result = s.retry_event(31, mode="now")
        print(f"Result: {result}")
        
        # Keep alive for background task
        print("Waiting 60s for background execution to catch up...")
        await asyncio.sleep(60)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
