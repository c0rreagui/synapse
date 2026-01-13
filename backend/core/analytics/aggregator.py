
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from datetime import datetime
from typing import Dict, List, Any
from core.session_manager import get_profile_metadata

class AnalyticsAggregator:
    def __init__(self):
        pass

    def get_profile_analytics(self, profile_id: str) -> Dict[str, Any]:
        """
        Aggregates metrics for a specific profile.
        Returns summary, history, and best_times.
        """
        metadata = get_profile_metadata(profile_id)
        
        if not metadata:
             return None

        # 1. Summary Metrics
        stats = metadata.get("stats", {}) # e.g., followerCount, heartCount
        
        # 2. Video Analysis (if available)
        videos = metadata.get("latest_videos", [])
        
        total_views = 0
        total_likes = 0
        total_comments = 0
        video_history = []
        
        for vid in videos:
            views = vid.get("stats", {}).get("playCount", 0)
            likes = vid.get("stats", {}).get("diggCount", 0)
            comments = vid.get("stats", {}).get("commentCount", 0)
            create_time = vid.get("createTime", 0) # Timestamp

            total_views += views
            total_likes += likes
            total_comments += comments
            
            # Date for history
            try:
                date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d')
                video_history.append({
                    "date": date_str,
                    "views": views,
                    "likes": likes,
                    "engagement": (likes + comments) / max(views, 1)
                })
            except:
                pass

        # Sort history by date
        video_history.sort(key=lambda x: x['date'])

        # Aggregate by day (summing up duplicates for same day)
        daily_history = {}
        for h in video_history:
            d = h['date']
            if d not in daily_history:
                daily_history[d] = {"date": d, "views": 0, "likes": 0}
            daily_history[d]["views"] += h['views']
            daily_history[d]["likes"] += h['likes']
            
        final_history = list(daily_history.values())
        final_history.sort(key=lambda x: x['date'])

        return {
            "profile_id": profile_id,
            "username": metadata.get("uniqueId"),
            "summary": {
                "followers": stats.get("followerCount", 0),
                "total_likes": stats.get("heartCount", 0),
                "total_views": total_views,
                "posts_analyzed": len(videos),
                "avg_engagement": (total_likes + total_comments) / max(total_views, 1) if total_views > 0 else 0
            },
            "history": final_history,
            "best_times": metadata.get("oracle_best_times", []) # Uses existing Oracle data
        }

analytics_service = AnalyticsAggregator()
