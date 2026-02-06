import asyncio
import sys
import os
import time

# Add root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "backend"))

async def test_lightweight_check():
    from core.session_manager import check_session_health_lightweight
    
    print("--- TESTING LIGHTWEIGHT PRE-FLIGHT ---")
    
    # Test profile (Opinião Viral) - We know it's invalid for upload from previous tests
    profile_id = "tiktok_profile_1770307556827"
    print(f"Testing profile {profile_id} (Lightweight)...")
    
    start = time.time()
    is_valid = await check_session_health_lightweight(profile_id)
    duration = time.time() - start
    
    print(f"Result: {'VALID' if is_valid else 'INVALID'}")
    print(f"Time taken: {duration:.2f}s (Should be much faster than browser)")

if __name__ == "__main__":
    asyncio.run(test_lightweight_check())
