"""
Voice Faculty - Content Generation
The voice of the Oracle. Generates captions, hashtags, bios, and replies.
Migrated from: seo_engine.py + community_manager.py
"""
import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VoiceFaculty:
    """
    The Voice: Content Generation Engine.
    Generates viral captions, hashtags, bio suggestions, and community replies.
    """

    def __init__(self, client):
        self.client = client

    async def generate_metadata(self, filename: str, niche: str = "General", duration: int = 0) -> Dict[str, Any]:
        """
        Generates viral caption and hashtags based on filename context.
        Used by Ingestion to pre-populate metadata.
        """
        if not self.client:
            return {"error": "Oracle Voice is offline"}

        logger.info(f"🎤 Oracle.Voice: Generating metadata for {filename}")

        prompt = f"""
        You are a TikTok SEO expert. Generate VIRAL metadata for this video.
        
        Filename: {filename}
        Niche: {niche}
        Duration: {duration}s
        
        Output JSON ONLY:
        {{
            "caption": "Legenda viral com emoji e CTA (máx 150 chars)",
            "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
            "hook_suggestion": "Sugestão de gancho para os primeiros 3 segundos",
            "best_time": "Melhor horário para postar (ex: 18h-20h)"
        }}
        
        RULES:
        1. Caption must include emojis and a call-to-action
        2. Mix trending hashtags with niche-specific ones
        3. Hook must create curiosity or FOMO
        4. Output in Brazilian Portuguese
        """

        try:
            response = self.client.generate_content(prompt)
            raw_text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(raw_text)
            result["faculty"] = "voice"
            return result
        except Exception as e:
            logger.error(f"❌ Oracle.Voice metadata failed: {e}")
            return {"error": str(e)}

    async def generate_bio(self, current_bio: str, niche: str) -> Dict[str, Any]:
        """
        Generates an optimized bio suggestion.
        """
        if not self.client:
            return {"error": "Oracle Voice is offline"}

        prompt = f"""
        Rewrite this TikTok bio to be more viral and engaging.
        
        Current Bio: {current_bio}
        Niche: {niche}
        
        Output JSON:
        {{
            "new_bio": "Nova bio otimizada (máx 80 chars)",
            "improvements": ["Melhoria 1", "Melhoria 2"],
            "score_before": 5,
            "score_after": 9
        }}
        """

        try:
            response = self.client.generate_content(prompt)
            raw_text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(raw_text)
            result["faculty"] = "voice"
            return result
        except Exception as e:
            return {"error": str(e)}

    async def generate_reply(self, comment_text: str, video_context: str = "", brand_voice: str = "friendly") -> Dict[str, Any]:
        """
        Generates a context-aware reply to a comment.
        """
        if not self.client:
            return {"error": "Oracle Voice is offline"}

        prompt = f"""
        Generate a reply to this TikTok comment.
        
        Comment: "{comment_text}"
        Video Context: {video_context}
        Brand Voice: {brand_voice}
        
        Output JSON:
        {{
            "reply": "Resposta natural e engajadora",
            "tone": "friendly/witty/professional",
            "emoji_used": true
        }}
        
        RULES:
        1. Sound human, not robotic
        2. Match the commenter's energy
        3. Include emoji if appropriate
        4. Keep it short (under 100 chars)
        """

        try:
            response = self.client.generate_content(prompt)
            raw_text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(raw_text)
            result["faculty"] = "voice"
            return result
        except Exception as e:
            return {"error": str(e)}

    async def audit_profile_seo(self, metadata: dict) -> Dict[str, Any]:
        """
        Multimodal audit of a profile (bio, username, avatar analysis).
        """
        if not self.client:
            return {"error": "Oracle Voice is offline"}

        username = metadata.get("username", "unknown")
        bio = metadata.get("bio", "")
        niche = metadata.get("niche", "General")

        prompt = f"""
        Perform an SEO audit for this TikTok profile.
        
        Username: @{username}
        Bio: {bio}
        Niche: {niche}
        
        Output JSON:
        {{
            "username_score": 8,
            "username_analysis": "Análise do username",
            "bio_score": 6,
            "bio_analysis": "Análise da bio",
            "suggested_bio": "Bio otimizada",
            "hashtag_strategy": ["#tag1", "#tag2"],
            "overall_score": 7,
            "top_recommendations": ["Rec 1", "Rec 2", "Rec 3"]
        }}
        """

        try:
            response = self.client.generate_content(prompt)
            raw_text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(raw_text)
            result["faculty"] = "voice"
            return result
        except Exception as e:
            return {"error": str(e)}
