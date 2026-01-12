from typing import Dict, List, Any
from datetime import datetime
import statistics
from core.session_manager import get_profile_metadata

class AnalyticsAggregator:
    
    def get_profile_analytics(self, profile_id: str) -> Dict[str, Any]:
        """
        Main entry point. Returns structured analytics for Frontend.
        """
        metadata = get_profile_metadata(profile_id)
        
        # Try to find video data in metadata or use mock
        # Oracle analysis might stick videos in "latest_videos" or similar
        videos = metadata.get("latest_videos", [])
        
        # If no real data, use SIMULATED data for MVP demonstration
        # In production, this would return empty or trigger a fetch
        if not videos:
            videos = self._generate_simulated_data()
            
        summary = self._calculate_summary(videos)
        history = self._build_history(videos)
        heatmap = self._build_heatmap(videos)
        
        return {
            "profile_id": profile_id,
            "summary": summary,
            "history": history,
            "heatmap": heatmap,
            "is_simulated": not metadata.get("latest_videos")
        }
    
    def _calculate_summary(self, videos: List[Dict]) -> Dict:
        if not videos:
            return {"total_views": 0, "avg_views": 0, "viral_ratio": 0}
            
        views = [v.get('stats', {}).get('playCount', 0) for v in videos]
        likes = [v.get('stats', {}).get('diggCount', 0) for v in videos]
        
        total_views = sum(views)
        avg_views = statistics.mean(views) if views else 0
        total_likes = sum(likes)
        
        # Viral Ratio: % of videos with > 2x average views
        viral_count = sum(1 for v in views if v > (avg_views * 2))
        viral_ratio = round(viral_count / len(videos), 2) if videos else 0
        
        engagement_rate = round(((total_likes) / total_views) * 100, 2) if total_views > 0 else 0
        
        return {
            "total_views": total_views,
            "avg_views": int(avg_views),
            "avg_likes": int(statistics.mean(likes)) if likes else 0,
            "viral_ratio": viral_ratio,
            "engagement_rate": engagement_rate
        }
        
    def _build_history(self, videos: List[Dict]) -> List[Dict]:
        """
        Returns sorted list of {date: 'ISO', views: 123, likes: 12}
        """
        # Sort by createTime
        sorted_vids = sorted(videos, key=lambda x: x.get('createTime', 0))
        
        history = []
        for v in sorted_vids:
            ts = v.get('createTime', 0)
            date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            
            history.append({
                "date": date_str,
                "views": v.get('stats', {}).get('playCount', 0),
                "likes": v.get('stats', {}).get('diggCount', 0)
            })
            
        return history
        
    def _build_heatmap(self, videos: List[Dict]) -> List[Dict]:
        """
        Returns 0-24h x 0-6d heatmap data.
        """
        # Initialize grid 7 days x 24 hours
        grid = {} # "Mon-14": [views, count]
        
        days_map = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        for v in videos:
            ts = v.get('createTime', 0)
            dt = datetime.fromtimestamp(ts)
            
            day_idx = int(dt.strftime('%w')) # 0=Sunday
            hour = dt.hour
            key = f"{day_idx}-{hour}"
            
            if key not in grid:
                grid[key] = {"views": [], "count": 0}
                
            grid[key]["views"].append(v.get('stats', {}).get('playCount', 0))
            grid[key]["count"] += 1
            
        # Format for frontend Recharts Scatter/Heatmap
        heatmap_data = []
        for key, data in grid.items():
            day_idx, hour = map(int, key.split('-'))
            avg_views = statistics.mean(data["views"])
            
            # Score 0-10 based on views (relative to something? or just raw?)
            # Let's return raw intensity and frontend allows filtering
            
            heatmap_data.append({
                "day": days_map[day_idx],
                "day_index": day_idx, # 0-6
                "hour": hour, # 0-23
                "value": int(avg_views),
                "count": data["count"]
            })
            
        return heatmap_data

    def _generate_simulated_data(self):
        """Generates realistic-looking mock data for MVP visualization."""
        import random
        import time
        
        data = []
        now = int(time.time())
        day_seconds = 86400
        
        # Generate 30 videos over last 30 days
        for i in range(30):
            # Random time of day
            hour_offset = random.randint(0, 86400)
            timestamp = now - ( (30-i) * day_seconds ) + hour_offset
            
            # Viral spikes
            is_viral = random.random() > 0.8
            base_views = random.randint(1000, 5000)
            views = base_views * random.randint(10, 50) if is_viral else base_views
            
            likes = int(views * random.uniform(0.05, 0.15))
            
            data.append({
                "id": f"sim_{i}",
                "desc": f"Video Simulado {i}",
                "createTime": timestamp,
                "stats": {
                    "playCount": views,
                    "diggCount": likes,
                    "commentCount": int(likes * 0.05),
                    "shareCount": int(likes * 0.1)
                }
            })
            
        return data

analytics_engine = AnalyticsAggregator()
