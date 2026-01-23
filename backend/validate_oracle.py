import asyncio
import os
import sys

# Add backend to path
sys.path.append("D:\\APPS - ANTIGRAVITY\\Synapse\\backend")

# Mock environment if needed
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GROQ_API_KEY")
print(f"Loaded Key: {key[:10]}...{key[-4:] if key else 'None'}")

from core.oracle.seo_engine import seo_engine
from core.oracle.deep_analytics import deep_analytics
from core.oracle.sentiment_pulse import sentiment_pulse

async def test_seo_engine():
    print("\n--- TEST: SEO Engine (SYN-10) ---")
    
    # 1. Test Keywords Suggestion
    print("1. Testing Keyword Suggestion (Groq)...")
    try:
        keywords = seo_engine.suggest_keywords("Digital Marketing")
        if "high_volume" in keywords:
            print("[OK] Keywords Generated:", keywords["high_volume"][:3])
        else:
            print("[WARN] Keywords format unexpected:", keywords)
    except Exception as e:
        print("[FAIL] Keywords Failed:", e)

    # 2. Test Content Gaps
    print("\n2. Testing Content Gaps (Groq)...")
    try:
        gaps = seo_engine.analyze_content_gaps("user_test", "Marketing")
        if "missing_formats" in gaps:
             print("[OK] Content Gaps Analysis:", gaps["missing_formats"][:2])
        else:
             print("[WARN] Gaps format unexpected")
    except Exception as e:
        print("[FAIL] Gaps Failed:", e)

async def test_deep_analytics():
    print("\n--- TEST: Deep Analytics (SYN-11) ---")
    
    # Mock Video Data
    video_data = {
        "id": "vid_123",
        "video": {"duration": 15},
        "stats": {
            "playCount": 10000,
            "diggCount": 2000,
            "shareCount": 500,
            "commentCount": 50
        }
    }
    
    print("1. Analyzing Retention & Viral Patterns...")
    try:
        result = deep_analytics.analyze_video_performance(video_data)
        metrics = result.get("deep_metrics", {})
        
        if "retention_curve" in metrics:
            print(f"[OK] Retention Curve Calculated ({len(metrics['retention_curve'])} points)")
        else:
            print("[FAIL] Retention Curve Missing")
            
        if "viral_score" in metrics:
            print(f"[OK] Viral Score: {metrics['viral_score']}")
            
        patterns = metrics.get("patterns", [])
        if patterns:
            print(f"[OK] Patterns Detected: {[p['name'] for p in patterns]}")
        else:
            print("[WARN] No patterns detected (might be expected)")
            
    except Exception as e:
        print("[FAIL] Deep Analytics Failed:", e)

async def test_sentiment_pulse():
    print("\n--- TEST: Sentiment Pulse (SYN-15) ---")
    
    # Mocking Sentiment Analysis (as it usually requires scraping)
    # We will test the Strategy Logic which is pure logic/LLM
    
    print("1. Testing Strategy Generation (Logic)...")
    try:
        strategy = sentiment_pulse.get_strategy_recommendations(85.0, 5.0)
        if "suggested_strategy" in strategy:
            print(f"[OK] Strategy: {strategy['suggested_strategy']}")
            print(f"[OK] Reasoning: {strategy['reasoning']}")
        else:
            print("[FAIL] Strategy Generation Failed")
            
    except Exception as e:
        print("[FAIL] Sentiment Logic Failed:", e)

async def main():
    print("Starting Oracle V2 Validation Tests...")
    
    # SEO
    await test_seo_engine()
    
    # Analytics
    await test_deep_analytics()
    
    # Sentiment
    await test_sentiment_pulse()
    
    print("\n[OK] Validation Complete.")

if __name__ == "__main__":
    asyncio.run(main())
