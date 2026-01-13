import asyncio
import sys
import json
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.profile_validator import validate_profile

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Profile ID required"}))
        return

    profile_id = sys.argv[1]
    try:
        result = await validate_profile(profile_id)
        # Use simple print for stdout capture
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
