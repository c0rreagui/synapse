import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.analytics.aggregator import analytics_engine

def test_on_engine():
    print("🧪 Testing Analytics Engine...")
    
    # Test with non-existent profile (Simulated Data)
    profile_id = "non_existent_profile_for_test"
    print(f"   [Step 1] Requesting analytics for '{profile_id}'...")
    
    data = analytics_engine.get_profile_analytics(profile_id)
    
    # Verify Structure
    assert "summary" in data, "❌ Missing summary"
    assert "history" in data, "❌ Missing history"
    assert "heatmap" in data, "❌ Missing heatmap"
    assert data["is_simulated"] is True, "❌ Should be simulated"
    
    print("   ✅ Structure looks correct.")
    
    # Verify Data Integrity
    summary = data["summary"]
    history = data["history"]
    heatmap = data["heatmap"]
    
    print(f"      - Total Views: {summary['total_views']}")
    print(f"      - Avg Views: {summary['avg_views']}")
    print(f"      - Viral Ratio: {summary['viral_ratio']}")
    print(f"      - History Points: {len(history)}")
    print(f"      - Heatmap Points: {len(heatmap)}")
    
    assert summary['total_views'] > 0, "❌ Simulated data should have views"
    assert len(history) == 30, "❌ Should have 30 days history"
    # Heatmap could comprise many cells, just check it's not empty
    assert len(heatmap) > 0, "❌ Heatmap empty"
    
    print("   ✅ Data integrity checks passed.")
    print("🎉 Analytics Engine Verified!")

if __name__ == "__main__":
    test_on_engine()
