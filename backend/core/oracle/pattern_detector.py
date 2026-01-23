from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class ViralPattern:
    name: str
    confidence: float # 0.0 - 1.0
    action_item: str
    description: str

class PatternDetector:
    """
    Detecta padrões de viralidade baseados em métricas avançadas.
    Ex: Share Explosion, Debate Spark, Short & Sticky.
    """

    def detect_patterns(self, stats: Dict[str, Any], deep_metrics: Dict[str, Any]) -> List[ViralPattern]:
        patterns = []
        
        play_count = stats.get('playCount', 0)
        share_count = stats.get('shareCount', 0)
        comment_count = stats.get('commentCount', 0)
        digg_count = stats.get('diggCount', 0)
        
        if play_count == 0:
            return []

        # 1. Share Explosion (Muitos compartilhamentos em relação a views)
        # Benchmark: > 1% de share rate é MUITO alto para TikTok
        share_rate = share_count / play_count
        if share_rate > 0.005: # > 0.5%
            patterns.append(ViralPattern(
                name="Share Explosion",
                confidence=min(1.0, share_rate * 100), # se 1% -> 1.0
                action_item="Conteúdo altamente compartilhável. Reposte em outras redes.",
                description=f"Taxa de compartilhamento ({share_rate:.2%}) muito acima da média."
            ))

        # 2. Discussion Spark (Muitos comments)
        comment_rate = comment_count / play_count
        if comment_rate > 0.002: # > 0.2%
             patterns.append(ViralPattern(
                name="Discussion Spark",
                confidence=min(1.0, comment_rate * 300), 
                action_item="Participe da discussão nos comentários para impulsionar.",
                description="O vídeo gerou debate intenso."
            ))
            
        # 3. Short & Sticky (Retenção alta em vídeo curto)
        completion_rate = deep_metrics.get("completion_rate", 0)
        # Assumimos que vídeos curtos tem retenção > 40% pra serem sticky
        if completion_rate > 40:
             patterns.append(ViralPattern(
                name="Short & Sticky",
                confidence=min(1.0, completion_rate / 100),
                action_item="Otimize o final (CTA) já que a maioria assiste até o fim.",
                description="Vídeo prendeu a atenção até o final."
            ))

        return patterns

pattern_detector = PatternDetector()
