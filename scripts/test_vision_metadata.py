import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from core.oracle.oracle import Oracle
from core.oracle.faculties.voice import VoiceFaculty
from core.oracle.faculties.vision import VisionFaculty

async def test_vision_metadata_integration():
    print("🧪 Testing Vision -> Voice Integration...")

    # 1. Setup Mock Oracle Client
    mock_client = MagicMock()
    mock_client.generate_content.return_value.text = '{"caption": "Test Caption", "hashtags": ["#test"], "hook_suggestion": "Hook", "best_time": "18h"}'
    
    # 2. Setup Vision Faculty with Mock
    vision = VisionFaculty(mock_client)
    # Mock analyze_unified so we don't need real video/API
    vision.analyze_unified = MagicMock(return_value={
        "visual_description": "A happy dog running in a park.",
        "frames_analyzed": 5
    })
    # Make it async compatible if needed (though MagicMock isn't async, we might need a coro)
    async def mock_analyze(*args, **kwargs):
        return {
            "visual_description": "A happy dog running in a park.",
            "frames_analyzed": 5
        }
    vision.analyze_unified = mock_analyze

    # 3. Setup Voice Faculty with injected Vision
    voice = VoiceFaculty(mock_client, vision_faculty=vision)

    # 4. Test generate_metadata WITH video_path
    print("\n[Case 1] With Video Path (Should trigger Vision)")
    result = await voice.generate_metadata(
        filename="dog_park.mp4",
        niche="Pets",
        duration=15,
        video_path="/tmp/dog_park.mp4" 
    )
    
    if result.get("vision_enhanced"):
        print("✅ Success: Vision context was used.")
        print(f"   Result keys: {result.keys()}")
    else:
        print("❌ Failed: 'vision_enhanced' flag missing.")
        print(result)

    # 5. Test generate_metadata WITHOUT video_path
    print("\n[Case 2] Without Video Path (Text Only)")
    result_no_video = await voice.generate_metadata(
        filename="dog_park.mp4",
        niche="Pets",
        duration=15
    )
    
    if not result_no_video.get("vision_enhanced"):
        print("✅ Success: Vision correctly skipped.")
    else:
        print("❌ Failed: Vision should not have run.")

if __name__ == "__main__":
    asyncio.run(test_vision_metadata_integration())
