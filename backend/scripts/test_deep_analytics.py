
import sys
import os
import json
from datetime import datetime, timedelta
import random
import io

# Force UTF-8 execution for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session_manager import update_profile_metadata, get_profile_metadata, import_session
from core.analytics.aggregator import analytics_service

TEST_PROFILE = "test_vibe_cortes"

def setup_test_data():
    print(f"🛠️ Setting up test profile: {TEST_PROFILE}")
    
    # 1. Create Profile if not exists
    if not get_profile_metadata(TEST_PROFILE):
        try:
            import_session("Vibe Cortes Test", "[]") # Creates generic
            # Rename/Fix slug manually or just use the one created?
            # session_manager.import_session returns the slug.
            # For simplicity, we assume update_profile_metadata works even if we just insert manually or use existing.
            # Actually import_session creates a random slug. 
            # Let's just update the specific test slug directly in DB or use a known existing one?
            # session_manager.py uses Profile model.
            pass
        except:
            pass

    # 2. Mock Videos
    # Pattern: 10 videos posted at 18:00 (Hour 18)
    # Pattern: High engagement (20% likes)
    
    base_time = datetime.now().replace(hour=18, minute=0, second=0)
    
    videos = []
    for i in range(10):
        # Video i
        videos.append({
            "createTime": (base_time - timedelta(days=i)).timestamp(), # One per day at 18:00
            "stats": {
                "playCount": 10000,
                "diggCount": 2000, # 20% engagement (High)
                "commentCount": 100
            },
            "description": "Short desc" if i < 5 else "Long description that is definitely more than fifty characters to test the pattern detector logic",
            "link": f"http://tiktok.com/@vibe/{i}"
        })
        
    updates = {
        "stats": {
            "followerCount": 50000,
            "heartCount": 100000,
            "videoCount": 10
        },
        "latest_videos": videos,
        "oracle_best_times": [{"day": 1, "hour": 18}]
    }
    
    # Write to DB
    # We need to ensure the profile exists in SQLite with this slug for this to work.
    # To avoid complexity, I will use a direct DB hack to ensure row exists.
    from core.database import SessionLocal
    from core.models import Profile
    db = SessionLocal()
    p = db.query(Profile).filter(Profile.slug == TEST_PROFILE).first()
    if not p:
        p = Profile(slug=TEST_PROFILE, label="Test Vibe", username="test_vibe", icon="🧪")
        db.add(p)
        db.commit()
    db.close()
    
    success = update_profile_metadata(TEST_PROFILE, updates)
    print(f"✅ Data injection status: {success}")

def verify_analytics():
    print("🔍 Verifying Analytics Result...")
    result = analytics_service.get_profile_analytics(TEST_PROFILE)
    
    if not result:
        print("❌ Failed to get analytics")
        return
        
    # 1. Check Heatmap
    heatmap = result.get("heatmap_data", [])
    peak_hour = max(heatmap, key=lambda x: x['intensity'])
    print(f"🔥 Heatmap Peak Hour: {peak_hour['hour']} (Expected: 18)")
    
    if peak_hour['hour'] == 18:
        print("✅ Heatmap Logic: PASS")
    else:
        print(f"❌ Heatmap Logic: FAIL (Got {peak_hour['hour']})")
        
    # 2. Check Retention Curve
    # We injected 20% engagement (2000 likes / 10000 views).
    # Logic: decay = 0.9 + (0.2 * 0.2) = 0.94
    # Curve at t=10 should be roughly 100 * (0.94 ^ 2) = 88%
    curve = result.get("retention_curve", [])
    val_10s = next((x['retention'] for x in curve if x['time'] == 10), 0)
    print(f"📉 Retention at 10s: {val_10s}% (Expected ~high due to 20% eng)")
    
    if val_10s > 80:
         print("✅ Retention Logic: PASS")
    else:
         print("❌ Retention Logic: FAIL (Too low)")

    # 3. Check Patterns
    patterns = result.get("patterns", [])
    print(f"🧩 Patterns Found: {[p['title'] for p in patterns]}")
    
    # We had 5 short videos with same stats, 5 long. 
    # Logic might not distinguish performance difference since stats were identical.
    # But it should verify code runs without error.
    if patterns:
        print("✅ Pattern Detector: PASS")
    else:
        print("⚠️ Pattern Detector: NO PATTERNS (Expected if data is uniform)")
        
    # 4. UTF-8 Check
    # Print a character to console
    print("🔣 Encoding Check: Acurácia (UTF-8)")

if __name__ == "__main__":
    setup_test_data()
    verify_analytics()
