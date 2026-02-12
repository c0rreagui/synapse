
import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.profile_validator import validate_profile
from core.session_manager import get_profile_user_agent

async def diag():
    profile_id = "tiktok_profile_1770135259969"
    ua = get_profile_user_agent(profile_id)
    print(f"Stored UA for {profile_id}: {ua}")
    
    # We can't easily peek inside validate_profile's browser without modifying it,
    # but we can check if it returns success.
    res = await validate_profile(profile_id, headless=True)
    print(f"Validation Result: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(diag())
