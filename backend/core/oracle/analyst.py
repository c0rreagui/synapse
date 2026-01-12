import logging
import json
from typing import Dict, Any
from core.oracle.client import oracle_client

logger = logging.getLogger(__name__)

class OracleAnalyst:
    """
    The Analyst: Brain of the Oracle.
    Processes raw data from the Collector and generates strategic insights using Gemini.
    """
    
    def __init__(self):
        self.client = oracle_client

    async def analyze_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a TikTok profile's raw data to determine viral strategy.
        """
        if not self.client:
            return {"error": "Oracle is offline"}

        logger.info(f"🧠 OracleAnalyst: Analyzing {profile_data.get('username')}...")

        # 1. Construct the Context
        # We convert the raw stats and video list into a clean JSON string for the LLM
        context_str = json.dumps(profile_data, indent=2)

        # 2. Design the System Prompt (Viral Strategist Persona)
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

        in your analysis, strictly follow this output format (JSON):
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
                {{
                    "type": "Visual",
                    "description": "Explicação detalhada do gancho visual usado"
                }},
                {{
                    "type": "Psychological",
                    "description": "Gatilho mental ativado (ex: curiosidade, FOMO)"
                }}
            ],
            "content_pillars": ["Tema 1", "Tema 2", "Tema 3"],
            "content_gaps": ["Oportunidade perdida 1", "Oportunidade perdida 2"],
            "performance_metrics": {{
                "avg_views_estimate": "15k - 50k",
                "engagement_rate_analysis": "Análise sobre a interação (comentários/shares)",
                "verified_video_count": 12,
                "comments_analyzed_count": {len(comments)}
            }},
            "suggested_next_video": {{
                "title": "Título Viral Sugerido",
                "concept": "Roteiro detalhado e conceito visual",
                "hook_script": "Sugestão de texto para os primeiros 3 segundos",
                "reasoning": "Por que isso vai funcionar"
            }},
            "sentiment_pulse": {{
                "score": 85,
                "dominant_emotion": "Curiosity/Hate/Love",
                "top_questions": ["Where can I buy this?", "Does it work on Android?"],
                "lovers": ["user1", "user2"],
                "haters": ["user3"],
                "debate_topic": "O que eles estão discutindo?"
            }},
            "best_times": [
                {{ "day": "Monday", "hour": 18, "reason": "High engagement window" }},
                {{ "day": "Wednesday", "hour": 12, "reason": "Lunch break peak" }}
            ]
        }}

        CRITICAL ANALYSIS RULES:
        1. **Check for 'Clips/Cortes'**: Look at the username and bio. If it contains "cortes", "clips", "talk", "podcast" and the content features different people, set "profile_type" to "Clips/Repost Channel".
        2. **Voice Analysis**: If it is a Clips channel, the "voice" is NOT the uploader's. It is "Borrowed". Do not say the uploader has a "jovial voice" if they are just reposting others.
        3. **Sentiment Pulse**: Read the COMMENTS. If there are mostly hate comments, score should be low. Identify specific questions users are asking.
        4. **Be Specific**: Avoid generic advice. Analyze the nuance of their lighting, editing, pacing, and storytelling.
        """

        try:
            # 3. Generate Insight
            response = self.client.generate_content(prompt)
            
            # 4. Parse Response (Expect JSON)
            # Gemini might return markdown ```json ... ``` so we clean it
            raw_text = response.text.strip()
            clean_text = raw_text.replace("```json", "").replace("```", "")
            
            metrics = json.loads(clean_text)
            
            return {
                "profile": profile_data.get("username"),
                "analysis": metrics,
                "raw_model": "gemini-pro"
            }

        except Exception as e:
            logger.error(f"❌ OracleAnalyst Failed: {e}")
            return {
                "error": str(e),
                "raw_response": response.text if 'response' in locals() else "No response"
            }

oracle_analyst = OracleAnalyst()
