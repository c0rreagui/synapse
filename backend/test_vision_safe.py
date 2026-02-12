
import sys
import os
import asyncio
import logging

# Setup paths
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_vision_safety():
    print("Testing VisionFaculty safety check...")
    try:
        from core.oracle.faculties.vision import VisionFaculty
        
        vision = VisionFaculty(client=None)
        
        # Test extract_frames with a fake path
        # Should NOT raise WinError, should just log error and return empty list
        frames = vision.extract_frames("dummy_path.mp4")
        
        print(f"Result: {frames}")
        
        if frames == []:
            print("SUCCESS: Returned empty list instead of crashing.")
        else:
            print("FAILURE: Unexpected return value.")
            
    except Exception as e:
        print(f"CRITICAL FAILURE: Crashed with {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vision_safety())
