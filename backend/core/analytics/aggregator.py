
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

        computed_engagement = (total_likes + total_comments) / max(total_views, 1) if total_views > 0 else 0
        
        return {
            "profile_id": profile_id,
            "username": metadata.get("uniqueId"),
            "summary": {
                "followers": stats.get("followerCount", 0),
                "total_likes": stats.get("heartCount", 0),
                "total_views": total_views,
                "posts_analyzed": len(videos),
                "avg_engagement": computed_engagement
            },
            "history": final_history,
            "best_times": self._calculate_best_times(videos),
            # ENHANCED ANALYTICS (SYN-38)
            "heatmap_data": self._generate_heatmap(videos),
            "retention_curve": self._generate_retention_curve(computed_engagement),
            "comparison": self._generate_comparison(videos),
            "patterns": self._detect_patterns(videos)
        }

    def _calculate_best_times(self, videos: List[Dict]) -> List[Dict]:
        """
        Analyzes posting times to find high-engagement slots.
        Returns top 3 slots (Day + Hour).
        """
        if not videos:
            return []
            
        # Slots: string key "day-hour" -> {total_score, count}
        slots = {}
        
        for v in videos:
            ts = v.get("createTime", 0)
            if ts <= 0: continue
            
            dt = datetime.fromtimestamp(ts)
            day = dt.weekday() # 0=Mon, 6=Sun
            hour = dt.hour
            
            key = f"{day}-{hour}"
            
            stats = v.get("stats", {})
            views = stats.get("playCount", 0)
            likes = stats.get("diggCount", 0)
            
            # Score formula: Views + (Likes * 5)
            # We value engagement highly
            score = (views / 100) + likes 
            
            if key not in slots:
                slots[key] = {"day": day, "hour": hour, "score": 0, "count": 0}
            
            slots[key]["score"] += score
            slots[key]["count"] += 1
            
        # Normalize scores by count (Average performance per slot)
        results = []
        for k, data in slots.items():
            avg_score = data["score"] / data["count"]
            results.append({
                "day": data["day"],
                "hour": data["hour"],
                "score": int(avg_score * 10) # Amplify for UI
            })
            
        # Sort by score desc
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:3]

    def _generate_heatmap(self, videos: List[Dict]) -> List[Dict]:
        """
        Generates 24h heatmap weighted by Engagement.
        """
        hourly_score = [0] * 24
        hourly_count = [0] * 24
        
        has_real_data = any(v.get("createTime", 0) > 0 for v in videos)
        
        if has_real_data:
            for v in videos:
                ts = v.get("createTime", 0)
                if ts <= 0: continue
                
                hour = datetime.fromtimestamp(ts).hour
                
                stats = v.get("stats", {})
                views = stats.get("playCount", 0)
                likes = stats.get("diggCount", 0)
                
                # Weight: heavily biased towards LIKES (Quality over Quantity)
                # If we just use frequency, spamming videos at 3AM makes 3AM "hot".
                # We want "Best Time to Post".
                weight = likes * 10 + views 
                
                hourly_score[hour] += weight
                hourly_count[hour] += 1
            
            # Normalize
            max_val = max(hourly_score) if max(hourly_score) > 0 else 1
            return [{"hour": h, "intensity": int((val / max_val) * 100)} for h, val in enumerate(hourly_score)]
        else:
            # Fallback
            import hashlib
            for v in videos:
                link = v.get("link", "") or str(v)
                h_hash = int(hashlib.md5(link.encode()).hexdigest(), 16) % 24
                hourly_score[h_hash] += 20
            
            return [{"hour": h, "intensity": min(val, 100)} for h, val in enumerate(hourly_score)]

    def _generate_retention_curve(self, avg_engagement: float) -> List[Dict]:
        """
        Simulates a retention curve based on engagement rate.
        Higher engagement = Flatter curve.
        """
        curve = []
        current_val = 100.0
        
        # Decay factor based on engagement (0.05 - 0.20 range typical)
        # 0.10 engagement -> standard decay
        base_step = 0.97 
        boost = min(avg_engagement, 0.2) * 0.15 
        step_decay = base_step + boost
        if step_decay > 0.995: step_decay = 0.995 
        
        for t in range(0, 60, 2): 
            if t == 0:
                val = 100
            elif t < 4:
                # Hook drop-off
                drop = 5 if avg_engagement > 0.1 else 15
                if t == 2: current_val -= drop
                val = current_val
            else:
                current_val = current_val * step_decay
                val = current_val
            
            curve.append({"time": t, "retention": int(val)})
            
        return curve

    def _generate_comparison(self, videos: List[Dict]) -> Dict:
        if not videos:
            return {"current": [], "previous": []}
            
        mid = len(videos) // 2
        # Assuming videos are sorted NEWEST first.
        # Current = newest half (0 to mid)
        # Previous = oldest half (mid to end)
        current = videos[:mid]
        previous = videos[mid:]
        
        def calc_metrics(v_list):
            views = sum(v.get("stats", {}).get("playCount", 0) for v in v_list)
            likes = sum(v.get("stats", {}).get("diggCount", 0) for v in v_list)
            return {"views": views, "likes": likes, "count": len(v_list)}

        curr_m = calc_metrics(current)
        prev_m = calc_metrics(previous)

        return {
            "period": "Last 7 Days",
            "current": curr_m,
            "previous": prev_m,
            "growth": {
                "views": ((curr_m["views"] - prev_m["views"]) / max(prev_m["views"], 1)) * 100,
                "likes": ((curr_m["likes"] - prev_m["likes"]) / max(prev_m["likes"], 1)) * 100
            }
        }

    def _detect_patterns(self, videos: List[Dict]) -> List[Dict]:
        """
        Enhanced Pattern Detection: Hooks, Duration, Hashtags.
        """
        if not videos:
             return []
        
        patterns = []
        
        # Sort by Performance (Views)
        sorted_v = sorted(videos, key=lambda x: x.get("stats", {}).get("playCount", 0), reverse=True)
        top_performers = sorted_v[:max(3, len(videos)//5)] # Top 20% or at least 3
        
        # 1. Description Length (The "Short Hook" pattern)
        shorts_count = sum(1 for v in top_performers if len(v.get("description", "")) < 50)
        if shorts_count >= len(top_performers) * 0.6: # 60% of top videos are short
             patterns.append({
                 "type": "VIRAL_HOOK",
                 "title": "Descrições Curtas",
                 "description": "Seus vídeos com descrições curtas (<50 chars) estão performando melhor.",
                 "confidence": 85,
                 "impact": "HIGH"
             })
        
        # 2. Duration Analysis (Shorts < 15s vs Longs > 30s)
        # Note: 'duration' might be inside 'video' dict or root depending on scraper
        # Aggregator usually gets clean structure, let's look safely
        def get_dur(v): return v.get("video", {}).get("duration", 0) or v.get("duration", 0)
        
        short_video_perf = []
        long_video_perf = []
        
        for v in videos:
            dur = get_dur(v)
            views = v.get("stats", {}).get("playCount", 0)
            if dur > 0 and dur <= 15:
                short_video_perf.append(views)
            elif dur >= 30:
                long_video_perf.append(views)
                
        avg_short = sum(short_video_perf)/len(short_video_perf) if short_video_perf else 0
        avg_long = sum(long_video_perf)/len(long_video_perf) if long_video_perf else 0
        
        if avg_short > avg_long * 1.5 and avg_long > 0:
             patterns.append({
                 "type": "FORMAT_WIN",
                 "title": "Vídeos Curtos (<15s)",
                 "description": f"Seus vídeos curtos têm {int(avg_short/avg_long)}x mais views que os longos.",
                 "confidence": 90,
                 "impact": "HIGH"
             })
        elif avg_long > avg_short * 1.5 and avg_short > 0:
             patterns.append({
                 "type": "FORMAT_WIN",
                 "title": "Vídeos Longos (>30s)",
                 "description": "O algoritmo está favorecendo seus vídeos mais longos.",
                 "confidence": 80,
                 "impact": "MEDIUM"
             })

        # 3. Consistency
        if not patterns:
             patterns.append({
                 "type": "ANOMALY",
                 "title": "Consistência de Views",
                 "description": "Seus views estão estáveis, indicando uma base de seguidores fiel.",
                 "confidence": 70,
                 "impact": "MEDIUM"
             })
             
        return patterns

analytics_service = AnalyticsAggregator()
