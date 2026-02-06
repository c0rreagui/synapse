import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from core.oracle.faculties.vision import VisionFaculty

async def test_aesthetics_analysis():
    print("🧪 Testing Vision Aesthetics Analysis (SYN-62)...")

    # 1. Setup Mock Oracle Client
    mock_client = MagicMock()
    mock_client.generate_content.return_value.text = '''{
        "aesthetics_score": 8,
        "visual_style": "Minimalist Dark",
        "color_palette": ["#000000", "#FF0050"],
        "branding_consistency": "High",
        "critique": "Strong consistent branding with high contrast.",
        "tips": ["Use more negative space."]
    }'''
    
    # 2. Setup Vision Faculty
    vision = VisionFaculty(mock_client)
    
    # 3. Create a dummy image for testing
    from PIL import Image
    dummy_path = "test_screenshot.jpg"
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(dummy_path)
    
    try:
        # 4. Run Analysis
        print(f"📸 analyzing {dummy_path}...")
        result = await vision.analyze_profile_aesthetics(dummy_path)
        
        print("\n📊 Result:")
        print(result)
        
        if result.get("aesthetics_score") == 8:
            print("✅ Success: Aesthetics score parsed correctly.")
        else:
            print("❌ Failed: Score mismatch.")
            
        if result.get("faculty") == "vision":
             print("✅ Success: Faculty identified.")
             
    finally:
        # Cleanup
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

if __name__ == "__main__":
    asyncio.run(test_aesthetics_analysis())
