"""
Oracle - Unified Intelligence System
The singular consciousness that orchestrates all AI capabilities of Synapse.
"""
import logging
from typing import Dict, Any, Optional

from core.oracle.client import oracle_client
from core.oracle.faculties.mind import MindFaculty
from core.oracle.faculties.vision import VisionFaculty
from core.oracle.faculties.voice import VoiceFaculty
from core.oracle.faculties.sense import SenseFaculty

logger = logging.getLogger(__name__)


class Oracle:
    """
    The Oracle: Unified AI Intelligence.
    
    A single entity with multiple faculties:
    - Mind:   Strategic analysis and insights
    - Vision: Visual content analysis
    - Voice:  Content generation (captions, hashtags, replies)
    - Sense:  Data collection and scraping
    """

    def __init__(self):
        self.client = oracle_client
        self.mind = MindFaculty(self.client)
        self.vision = VisionFaculty(self.client)
        self.voice = VoiceFaculty(self.client)
        self.sense = SenseFaculty()
        
        logger.info("🔮 Oracle initialized with all faculties active.")

    def is_online(self) -> bool:
        """Check if Oracle has LLM connection."""
        return self.client is not None and self.client.is_online()

    def ping(self) -> Dict[str, Any]:
        """Health check for Oracle."""
        return {
            "status": "online" if self.is_online() else "offline",
            "faculties": {
                "mind": "active",
                "vision": "active",
                "voice": "active",
                "sense": "active"
            },
            "engine": self.client.get_engine_name() if self.client else "none"
        }

    # ========== HIGH-LEVEL ORCHESTRATED METHODS ==========

    async def full_scan(self, username: str) -> Dict[str, Any]:
        """
        Complete profile analysis using all faculties.
        1. Sense collects raw data
        2. Mind analyzes strategy
        3. Returns unified insights
        """
        logger.info(f"🔮 Oracle.full_scan: Initiating full scan for @{username}")

        # Step 1: Collect data (Sense)
        profile_data = await self.sense.collect_profile(username)
        if "error" in profile_data:
            return {"error": f"Sense failed: {profile_data['error']}"}

        # Step 2: Collect comments from top video
        if profile_data.get("videos"):
            top_video = profile_data["videos"][0]
            if top_video.get("link"):
                comments = await self.sense.collect_comments(top_video["link"])
                profile_data["comments"] = comments

        # Step 3: Strategic analysis (Mind)
        analysis = await self.mind.analyze_profile(profile_data)

        return {
            "username": username,
            "raw_data": profile_data,
            "strategic_analysis": analysis.get("analysis", {}),
            "scan_type": "full",
            "faculties_used": ["sense", "mind"]
        }

    async def analyze_video_for_upload(self, video_path: str, profile_id: str) -> Dict[str, Any]:
        """
        Analyzes a video before upload.
        1. Vision extracts and analyzes frames
        2. Voice generates metadata
        Returns enriched metadata.
        """
        logger.info(f"🔮 Oracle.analyze_video: Processing {video_path}")

        # Step 1: Visual analysis
        visual_result = await self.vision.analyze_video(video_path)

        # Step 2: Generate metadata
        import os
        filename = os.path.basename(video_path)
        metadata_result = await self.voice.generate_metadata(filename)

        return {
            "video_path": video_path,
            "profile_id": profile_id,
            "visual_analysis": visual_result.get("visual_analysis", ""),
            "suggested_caption": metadata_result.get("caption", ""),
            "suggested_hashtags": metadata_result.get("hashtags", []),
            "hook_suggestion": metadata_result.get("hook_suggestion", ""),
            "faculties_used": ["vision", "voice"]
        }

    async def audit_profile(self, profile_id: str, metadata: dict) -> Dict[str, Any]:
        """
        SEO audit of a profile.
        Uses Voice faculty for analysis.
        """
        logger.info(f"🔮 Oracle.audit_profile: Auditing {profile_id}")
        return await self.voice.audit_profile_seo(metadata)

    async def spy_competitor(self, target_username: str) -> Dict[str, Any]:
        """
        Deep spy on a competitor.
        1. Sense collects all data
        2. Mind analyzes strategy
        """
        logger.info(f"🔮 Oracle.spy_competitor: Spying on @{target_username}")

        spy_data = await self.sense.spy_competitor(target_username)
        if "error" in spy_data:
            return spy_data

        analysis = await self.mind.analyze_profile(spy_data)

        return {
            "target": target_username,
            "raw_data": spy_data,
            "strategic_analysis": analysis.get("analysis", {}),
            "mode": "competitor_spy",
            "faculties_used": ["sense", "mind"]
        }

    async def generate_reply(self, comment: str, context: str = "") -> Dict[str, Any]:
        """
        Generate a reply to a comment using Voice faculty.
        """
        return await self.voice.generate_reply(comment, context)

    # ========== DIRECT FACULTY ACCESS (for granular control) ==========

    async def use_mind(self, profile_data: dict) -> Dict[str, Any]:
        """Direct access to Mind faculty."""
        return await self.mind.analyze_profile(profile_data)

    async def use_vision(self, video_path: str) -> Dict[str, Any]:
        """Direct access to Vision faculty."""
        return await self.vision.analyze_video(video_path)

    async def use_voice(self, action: str, **kwargs) -> Dict[str, Any]:
        """Direct access to Voice faculty."""
        if action == "metadata":
            return await self.voice.generate_metadata(**kwargs)
        elif action == "bio":
            return await self.voice.generate_bio(**kwargs)
        elif action == "reply":
            return await self.voice.generate_reply(**kwargs)
        elif action == "audit":
            return await self.voice.audit_profile_seo(**kwargs)
        return {"error": f"Unknown voice action: {action}"}

    async def use_sense(self, action: str, **kwargs) -> Dict[str, Any]:
        """Direct access to Sense faculty."""
        if action == "profile":
            return await self.sense.collect_profile(**kwargs)
        elif action == "comments":
            return await self.sense.collect_comments(**kwargs)
        elif action == "spy":
            return await self.sense.spy_competitor(**kwargs)
        return {"error": f"Unknown sense action: {action}"}


# Singleton instance
oracle = Oracle()
