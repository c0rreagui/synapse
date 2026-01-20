"""
Sentiment Pulse - Comment Sentiment Analysis
Analyzes TikTok comments to determine audience sentiment and suggest content strategies.
"""
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from core.oracle.client import oracle_client
from core.oracle.faculties.sense import SenseFaculty

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    dominant_emotion: str
    top_topics: List[str]
    suggested_strategy: str
    strategy_examples: List[str]
    lovers: List[str]
    haters: List[str]
    analyzed_at: str


class SentimentPulse:
    """
    Sentiment Pulse Engine.
    Analyzes comment sentiment to guide content strategy.
    """
    
    STRATEGY_THRESHOLDS = {
        "positive_high": 80,   # >80% positive = CTAs de crescimento
        "negative_high": 40,   # >40% negative = Legendas polêmicas
    }
    
    STRATEGY_TEMPLATES = {
        "growth_cta": {
            "name": "CTAs de Crescimento",
            "examples": [
                "Siga para mais conteúdo assim!",
                "Marque um amigo que precisa ver isso",
                "Comenta ai o que quer ver no próximo",
                "Salva pra não perder!"
            ]
        },
        "controversy": {
            "name": "Legendas Polêmicas",
            "examples": [
                "Falem mal, mas falem de mim",
                "POV: Você fazendo todo mundo discordar",
                "Isso vai dividir opiniões...",
                "Será que só eu penso assim?"
            ]
        },
        "educational": {
            "name": "Conteúdo Educativo",
            "examples": [
                "Vou explicar porque...",
                "Resposta aos comentários",
                "Entenda de uma vez por todas",
                "O que ninguém te contou sobre..."
            ]
        }
    }
    
    def __init__(self):
        self.sense = SenseFaculty()
        self.client = oracle_client
    
    async def analyze_profile_sentiment(self, username: str, max_comments: int = 50) -> Dict[str, Any]:
        """
        Analyze sentiment of comments on a profile's latest videos.
        
        Args:
            username: TikTok username
            max_comments: Maximum comments to analyze
            
        Returns:
            SentimentResult as dict
        """
        logger.info(f"💬 Analyzing sentiment for @{username}...")
        
        # Step 1: Collect profile data to get video URLs
        profile_data = await self.sense.collect_profile(username)
        
        if "error" in profile_data:
            return {"error": f"Failed to collect profile: {profile_data['error']}"}
        
        videos = profile_data.get("videos", [])
        if not videos:
            return {"error": "No videos found on profile"}
        
        # Step 2: Collect comments from top videos
        all_comments = []
        for video in videos[:3]:  # Top 3 videos
            video_url = video.get("link", "")
            if video_url:
                comments = await self.sense.collect_comments(video_url, max_comments=max_comments // 3)
                all_comments.extend(comments)
        
        if not all_comments:
            return {"error": "No comments found"}
        
        logger.info(f"📝 Collected {len(all_comments)} comments for analysis")
        
        # Step 3: Analyze with LLM
        return await self._analyze_with_llm(all_comments)
    
    async def analyze_video_sentiment(self, video_url: str, max_comments: int = 50) -> Dict[str, Any]:
        """
        Analyze sentiment of comments on a specific video.
        
        Args:
            video_url: TikTok video URL
            max_comments: Maximum comments to analyze
            
        Returns:
            SentimentResult as dict
        """
        logger.info(f"💬 Analyzing sentiment for video: {video_url}")
        
        # Collect comments
        comments = await self.sense.collect_comments(video_url, max_comments=max_comments)
        
        if not comments:
            return {"error": "No comments found"}
        
        logger.info(f"📝 Collected {len(comments)} comments for analysis")
        
        return await self._analyze_with_llm(comments)
    
    async def _analyze_with_llm(self, comments: List[Dict[str, str]]) -> Dict[str, Any]:
        """Send comments to LLM for sentiment analysis."""
        
        if not self.client:
            return {"error": "Oracle client offline"}
        
        # Prepare comments for prompt
        comments_text = json.dumps(comments[:50], ensure_ascii=False)  # Limit to 50
        
        prompt = f"""
        Você é um analista de sentimento especializado em TikTok.
        
        Analise os seguintes comentários e classifique o sentimento geral da audiência.
        
        COMENTÁRIOS:
        {comments_text}
        
        Retorne APENAS JSON válido no seguinte formato:
        {{
            "positive_count": 10,
            "negative_count": 5,
            "neutral_count": 3,
            "dominant_emotion": "Curiosidade | Amor | Ódio | Confusão | Diversão",
            "top_topics": ["Tópico 1", "Tópico 2", "Tópico 3"],
            "lovers": ["@user1", "@user2"],
            "haters": ["@user3"],
            "debate_topic": "O que estão discutindo nos comentários?"
        }}
        
        REGRAS:
        1. Considere emojis como indicadores (❤️😍 = positivo, 😤🤮 = negativo)
        2. Ignore comentários muito curtos (1-2 palavras)
        3. "lovers" = usuários muito engajados positivamente
        4. "haters" = usuários críticos ou negativos
        """
        
        try:
            response = self.client.generate_content(prompt)
            raw_text = response.text.strip()
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON with fallback
            try:
                analysis = json.loads(clean_text)
            except json.JSONDecodeError:
                # Regex fallback
                json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    return {"error": "Failed to parse LLM response"}
            
            # Calculate percentages
            total = analysis["positive_count"] + analysis["negative_count"] + analysis["neutral_count"]
            if total == 0:
                total = 1
            
            positive_pct = (analysis["positive_count"] / total) * 100
            negative_pct = (analysis["negative_count"] / total) * 100
            neutral_pct = (analysis["neutral_count"] / total) * 100
            
            # Determine strategy
            strategy = self._determine_strategy(positive_pct, negative_pct)
            
            result = SentimentResult(
                positive_count=analysis["positive_count"],
                negative_count=analysis["negative_count"],
                neutral_count=analysis["neutral_count"],
                positive_pct=round(positive_pct, 1),
                negative_pct=round(negative_pct, 1),
                neutral_pct=round(neutral_pct, 1),
                dominant_emotion=analysis.get("dominant_emotion", "Unknown"),
                top_topics=analysis.get("top_topics", []),
                suggested_strategy=strategy["name"],
                strategy_examples=strategy["examples"],
                lovers=analysis.get("lovers", []),
                haters=analysis.get("haters", []),
                analyzed_at=datetime.now().isoformat()
            )
            
            logger.info(f"✅ Sentiment analysis complete: {positive_pct:.0f}% positive")
            return asdict(result)
            
        except Exception as e:
            logger.error(f"❌ Sentiment analysis failed: {e}")
            return {"error": str(e)}
    
    def _determine_strategy(self, positive_pct: float, negative_pct: float) -> Dict[str, Any]:
        """Determine content strategy based on sentiment percentages."""
        
        if positive_pct >= self.STRATEGY_THRESHOLDS["positive_high"]:
            return self.STRATEGY_TEMPLATES["growth_cta"]
        elif negative_pct >= self.STRATEGY_THRESHOLDS["negative_high"]:
            return self.STRATEGY_TEMPLATES["controversy"]
        else:
            return self.STRATEGY_TEMPLATES["educational"]
    
    def get_strategy_recommendations(self, positive_pct: float, negative_pct: float) -> Dict[str, Any]:
        """Get strategy recommendations based on percentages (without scraping)."""
        strategy = self._determine_strategy(positive_pct, negative_pct)
        
        return {
            "positive_pct": positive_pct,
            "negative_pct": negative_pct,
            "suggested_strategy": strategy["name"],
            "strategy_examples": strategy["examples"],
            "reasoning": self._get_reasoning(positive_pct, negative_pct)
        }
    
    def _get_reasoning(self, positive_pct: float, negative_pct: float) -> str:
        """Generate reasoning for strategy recommendation."""
        if positive_pct >= 80:
            return "Audiência muito positiva! Aproveite para CTAs de crescimento."
        elif negative_pct >= 40:
            return "Engajamento polarizado. Use isso a seu favor com legendas polêmicas."
        else:
            return "Audiência balanceada. Foque em conteúdo educativo para construir autoridade."


# Singleton instance
sentiment_pulse = SentimentPulse()
