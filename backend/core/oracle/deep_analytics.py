from typing import Dict, Any, Optional
from core.oracle.retention_curve import retention_analyzer, RetentionAnalysis
from core.oracle.pattern_detector import pattern_detector, ViralPattern
from dataclasses import asdict

class DeepAnalytics:
    """
    Motor de Analytics Profundo do Oracle V2.
    Responsável por métricas avançadas, retenção e detecção de padrões.
    """
    
    def analyze_video_performance(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa performance de um vídeo específico.
        Espera video_data contendo: duration, stats (diggCount, playCount, etc)
        """
        stats = video_data.get('stats', {})
        play_count = stats.get('playCount', 0)
        digg_count = stats.get('diggCount', 0)
        share_count = stats.get('shareCount', 0)
        comment_count = stats.get('commentCount', 0)
        duration = video_data.get('video', {}).get('duration', 0)

        if not play_count or not duration:
            return {"error": "Insufficient data"}

        # Calcular Engagement Rate
        interactions = digg_count + share_count + comment_count
        engagement_rate = interactions / play_count if play_count > 0 else 0
        
        # Gerar análise de retenção
        retention: RetentionAnalysis = retention_analyzer.analyze_curve(
            duration=duration,
            total_views=play_count,
            engagement_score=engagement_rate
        )

        # Deep Metrics preliminares para o pattern detector
        deep_metrics_pre = {
            "retention_curve": retention.curve, # Objeto puro
            "completion_rate": retention.completion_rate
        }

        # Detectar Padrões
        patterns = pattern_detector.detect_patterns(stats, deep_metrics_pre)

        return {
            "video_id": video_data.get('id'),
            "basic_stats": {
                "views": play_count,
                "likes": digg_count,
                "shares": share_count,
                "comments": comment_count,
                "engagement_rate": round(engagement_rate * 100, 2)
            },
            "deep_metrics": {
                "retention_curve": [asdict(p) for p in retention.curve],
                "average_watch_time": retention.average_watch_time,
                "completion_rate": retention.completion_rate,
                "drop_off_seconds": retention.drop_off_points,
                "viral_score": self._calculate_viral_score(play_count, engagement_rate),
                "patterns": [asdict(p) for p in patterns]
            },
            "insights": self._generate_insights(retention, engagement_rate, patterns)
        }

    def _calculate_viral_score(self, views: int, engagement: float) -> int:
        """Calcula score viral de 0 a 100"""
        # Exemplo simples
        view_score = min(50, (views / 10000) * 10)
        eng_score = min(50, (engagement * 100) * 2)
        return int(view_score + eng_score)

    def _generate_insights(self, retention: RetentionAnalysis, engagement: float, patterns: list) -> list:
        insights = []
        if retention.completion_rate > 20:
            insights.append("Alta taxa de conclusão indicando ótimo hook e conteúdo.")
        if engagement > 0.10:
            insights.append("Engajamento excepcional. Considere repostar.")
        if retention.drop_off_points and 0 in retention.drop_off_points:
            insights.append("Perda significativa no primeiro segundo. Melhore o Hook visual.")
        
        for p in patterns:
            insights.append(f"Padrão Detectado: {p.name} - {p.action_item}")
        
        return insights

deep_analytics = DeepAnalytics()
