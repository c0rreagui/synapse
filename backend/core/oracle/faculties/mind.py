"""
Mind Faculty - Strategic Analysis
The analytical brain of the Oracle. Processes profile data and generates strategic insights.
Migrated from: analyst.py
"""
import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MindFaculty:
    """
    The Mind: Strategic Analysis Engine.
    Processes raw data and generates viral strategy insights using LLM.
    """

    def __init__(self, client):
        self.client = client

    async def analyze_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a TikTok profile's raw data to determine viral strategy.
        """
        if not self.client:
            return {"error": "Oracle Mind is offline"}

        logger.info(f"🧠 Oracle.Mind: Analyzing {profile_data.get('username')}...")

        context_str = json.dumps(profile_data, indent=2)
        comments = profile_data.get("comments", [])
        comments_text = json.dumps(comments, indent=2) if comments else "No comments retrieved."

        prompt = f"""
        You are The Oracle, an elite Viral Content Strategist for TikTok.
        Your goal is to perform a DEEP DIVE analysis of the following profile.
        
        IMPORTANT: Your output language is Brazilian Portuguese (PT-BR).
        
        PROFILE DATA:
        {context_str}

        LATEST VIDEO COMMENTS (Voice of the People):
        {comments_text}

        Output ONLY valid JSON in this exact format:
        {{
            "profile_type": "Original Creator | Clips/Repost Channel | Brand/Business | Fan Account",
            "voice_authenticity": "High | Low | Borrowed (Clips)",
            "summary": "Resumo executivo da marca e voz do criador (2-3 frases)",
            "virality_score": 8.5,
            "engagement_quality": "High/Medium/Low",
            "audience_persona": {{
                "demographics": "Ex: Gen Z, Mulheres 18-24",
                "psychographics": "Interesses, dores e desejos do público",
                "pain_points": ["Dor 1", "Dor 2"]
            }},
            "viral_hooks": [
                {{"type": "Visual", "description": "Explicação do gancho visual"}},
                {{"type": "Psychological", "description": "Gatilho mental ativado"}}
            ],
            "content_pillars": ["Tema 1", "Tema 2", "Tema 3"],
            "content_gaps": ["Oportunidade 1", "Oportunidade 2"],
            "performance_metrics": {{
                "avg_views_estimate": "15k - 50k",
                "engagement_rate_analysis": "Análise sobre a interação",
                "verified_video_count": 12,
                "comments_analyzed_count": {len(comments)}
            }},
            "suggested_next_video": {{
                "title": "Título Viral Sugerido",
                "concept": "Roteiro detalhado",
                "hook_script": "Texto para os primeiros 3 segundos",
                "reasoning": "Por que vai funcionar"
            }},
            "sentiment_pulse": {{
                "score": 85,
                "dominant_emotion": "Curiosity/Hate/Love",
                "top_questions": ["Pergunta 1?", "Pergunta 2?"],
                "lovers": ["user1"],
                "haters": ["user2"],
                "debate_topic": "O que estão discutindo?"
            }},
            "best_times": [
                {{"day": "Segunda", "hour": 12, "reason": "Razão específica baseada no nicho e público"}},
                {{"day": "Quarta", "hour": 19, "reason": "Horário de pico para este tipo de conteúdo"}},
                {{"day": "Sábado", "hour": 21, "reason": "Comportamento do público-alvo neste dia"}}
            ]
        }}

        CRITICAL RULES:
        1. If username contains "cortes", "clips", set profile_type to "Clips/Repost Channel".
        2. If Clips channel, voice_authenticity = "Borrowed".
        3. Analyze COMMENTS for sentiment. If mostly hate, score low.
        4. Be specific about lighting, editing, pacing.
        5. For best_times: Consider the NICHE and AUDIENCE TYPE. Gaming/entertainment = evenings. Educational = lunch breaks. Lifestyle = weekends. Give 3-5 specific times with UNIQUE reasons for each, not generic "high engagement". Consider Brazilian timezone (GMT-3).
        """

        try:
            response = self.client.generate_content(prompt)
            raw_text = response.text.strip()
            clean_text = raw_text.replace("```json", "").replace("```", "")
            metrics = json.loads(clean_text)

            return {
                "profile": profile_data.get("username"),
                "analysis": metrics,
                "faculty": "mind"
            }

        except Exception as e:
            logger.error(f"❌ Oracle.Mind failed: {e}")
            return {
                "error": str(e),
                "raw_response": response.text if 'response' in locals() else "No response"
            }
