import script_env
script_env.setup_script_env()

import asyncio
from core.scheduler import Scheduler

async def main():
    scheduler = Scheduler()
    print("Triggering check_due_items()...")
    await scheduler.check_due_items()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
