from dataclasses import dataclass
from typing import List, Dict, Optional
import random
import math

@dataclass
class RetentionPoint:
    seconds: int
    percentage: float

@dataclass
class RetentionAnalysis:
    curve: List[RetentionPoint]
    average_watch_time: float
    completion_rate: float
    drop_off_points: List[int]  # Segundos onde houve queda brusca

class RetentionAnalyzer:
    """
    Analisa e gera dados de retenção para vídeos.
    Nota: Em um cenário real sem API oficial do TikTok com acesso a analytics privados,
    nós estimamos a curva baseada em métricas públicas (likes, shares, comments vs views)
    ou usamos dados mockados realistas para demonstração.
    """

    def analyze_curve(self, duration: int, total_views: int, engagement_score: float) -> RetentionAnalysis:
        """
        Gera uma curva de retenção baseada no score de engajamento.
        Engagement Score alto = curva mais plana (melhor retenção).
        """
        curve = []
        
        # O início é sempre 100%
        current_retention = 100.0
        
        # Fator de decaimento baseado no engajamento (0.0 a 1.0)
        # Se engajamento é alto (0.1), decaimento é baixo. Se baixo (0.01), decaimento alto.
        # Normalizando score típico de 0-10% para um fator
        decay_factor = max(0.90, min(0.99, 0.90 + engagement_score))
        
        # Drop inicial brusco (hook failure rate padrão)
        hook_retention = 0.85 + (engagement_score * 2) # Melhor engajamento = melhor hook
        hook_retention = min(0.98, hook_retention)
        
        for second in range(duration + 1):
            if second == 0:
                curve.append(RetentionPoint(0, 100.0))
                continue
                
            if second == 1:
                current_retention = hook_retention * 100
            else:
                # Decaimento natural + variabilidade aleatória pequena
                drop = random.uniform(0, 1.0) * (1 - decay_factor)
                current_retention *= (1 - drop)
            
            # Garante que não sobe (retenção sempre cai ou mantem, exceto replay que não modelamos aqui simples)
            current_retention = max(0.0, current_retention)
            curve.append(RetentionPoint(second, round(current_retention, 1)))

        # Calcular estatísticas derivadas
        avg_watch_time = sum(p.percentage for p in curve) / 100 # Aproximação grosseira
        completion_rate = curve[-1].percentage
        
        # Detectar drop-offs (> 5% de queda em 1s)
        drop_offs = []
        for i in range(1, len(curve)):
            if curve[i-1].percentage - curve[i].percentage > 5.0:
                drop_offs.append(i)

        return RetentionAnalysis(
            curve=curve,
            average_watch_time=round(avg_watch_time, 1),
            completion_rate=round(completion_rate, 1),
            drop_off_points=drop_offs
        )

# Instância singleton
retention_analyzer = RetentionAnalyzer()
