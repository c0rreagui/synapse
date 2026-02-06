
import sys
import os
import asyncio
import json
from pprint import pprint

# Fix path to include backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.oracle.analytics_aggregator import analytics_aggregator
from core.session_manager import import_session, update_profile_metadata, delete_session

async def test_aggregator():
    print("Testing Analytics Aggregator...")

    # 1. Create Mock Profile via DB
    # We use import_session to create a valid DB entry
    try:
        profile_id = import_session(
            label="Test Analytics User", 
            cookies_json="[]", 
            username="test_vm_user"
        )
        print(f"Created temporary profile: {profile_id}")
    except Exception as e:
        print(f"Failed to create profile: {e}")
        return

    try:
        mock_videos = [
            {
                "id": "v1",
                "createTime": 1700000000,
                "stats": {"playCount": 10000, "diggCount": 2000, "commentCount": 50, "shareCount": 100},
                "video": {"duration": 30}
            },
            {
                "id": "v2",
                "createTime": 1700003600, # +1 hour
                "stats": {"playCount": 5000, "diggCount": 100, "commentCount": 10, "shareCount": 5},
                "video": {"duration": 15}
            }
        ]

        # 2. Populate Metadata (Videos)
        update_profile_metadata(profile_id, {
            "latest_videos": mock_videos,
            "stats": {"followerCount": 50000, "heartCount": 100000},
            "oracle_best_times": [{"day": "Monday", "hour": 18}]
        })

        # 3. Run Aggregator
        data = analytics_aggregator.get_dashboard_data(profile_id)
        
        if "error" in data:
            print(f"Aggregator returned error: {data['error']}")
        else:
            print("\nAggregator Success!")
            print(f"User: {data['username']}")
            print(f"Summary: {data['summary']}")
            print(f"Heatmap (Len): {len(data['heatmap_data'])}")
            
            # Assertions
            if not data['retention_curve']:
                print("Warning: Retention curve empty (expected for mocked deep analytics)")
            else:
                 print(f"Retention Point 0: {data['retention_curve'][0]}")
                 
            assert "summary" in data
            assert data['summary']['total_views'] == 15000
    
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print(f"Cleaning up {profile_id}...")
        delete_session(profile_id)

if __name__ == "__main__":
    asyncio.run(test_aggregator())
