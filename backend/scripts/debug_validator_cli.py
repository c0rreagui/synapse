import asyncio
import sys
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Add root to path
sys.path.append(os.getcwd())

async def run_debug():
    from backend.core.profile_validator import validate_profile
    
    print("--- DEBUGGING VALIDATOR ---")
    try:
        # Test with profile 01
        result = await validate_profile("tiktok_profile_01")
        print(f"RESULT: {result}")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
