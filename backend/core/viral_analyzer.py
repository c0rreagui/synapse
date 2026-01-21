"""
🧠 Viral Analyzer - Motor de Análise de Crescimento
Calcula viral_score e detecta sons que estão "explodindo"
"""
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

DATA_DIR = "data/viral_sounds"
ANALYSIS_FILE = f"{DATA_DIR}/analysis.json"


@dataclass
class SoundAnalysis:
    """Análise detalhada de um som"""
    sound_id: str
    title: str
    author: str
    
    # Métricas atuais
    current_usage: int
    current_rank: int
    
    # Métricas de crescimento
    growth_1h: float = 0.0   # % crescimento última hora
    growth_6h: float = 0.0   # % crescimento últimas 6h
    growth_24h: float = 0.0  # % crescimento últimas 24h
    
    # Score composto
    viral_score: float = 0.0
    
    # Classificação
    status: str = "normal"  # normal, rising, exploding
    alert_triggered: bool = False
    
    # Metadata
    analyzed_at: str = ""
    niche: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


class ViralAnalyzer:
    """
    Motor de análise que calcula scores de viralidade
    baseado em múltiplas métricas de crescimento.
    """
    
    # Thresholds de classificação
    EXPLODING_THRESHOLD = 85.0
    RISING_THRESHOLD = 60.0
    
    # Pesos para cálculo do viral_score
    WEIGHTS = {
        "growth_1h": 0.45,   # Crescimento recente é mais importante
        "growth_6h": 0.30,
        "growth_24h": 0.15,
        "rank_bonus": 0.10
    }
    
    def __init__(self):
        self._ensure_dirs()
        self._alerts_sent: set = set()  # Evita alertas duplicados
    
    def _ensure_dirs(self):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def analyze(self, sounds: List[Dict], history: List[Dict]) -> List[SoundAnalysis]:
        """
        Analisa lista de sons e calcula scores de viralidade.
        
        Args:
            sounds: Lista de sons atuais (do scraper)
            history: Histórico de snapshots anteriores
            
        Returns:
            Lista de SoundAnalysis com scores calculados
        """
        analyses = []
        now = datetime.now()
        
        # Indexar histórico por timestamp
        history_by_time = self._index_history(history)
        
        for sound in sounds:
            analysis = SoundAnalysis(
                sound_id=sound.get("id", ""),
                title=sound.get("title", ""),
                author=sound.get("author", ""),
                current_usage=sound.get("usage_count", 0),
                current_rank=sound.get("rank", 99),
                analyzed_at=now.isoformat()
            )
            
            # Calcular crescimentos
            analysis.growth_1h = self._calculate_growth(
                sound, history_by_time, hours=1
            )
            analysis.growth_6h = self._calculate_growth(
                sound, history_by_time, hours=6
            )
            analysis.growth_24h = self._calculate_growth(
                sound, history_by_time, hours=24
            )
            
            # Calcular viral_score
            analysis.viral_score = self._calculate_viral_score(analysis)
            
            # Classificar status
            analysis.status = self._classify_status(analysis.viral_score)
            
            # Verificar se deve disparar alerta
            analysis.alert_triggered = self._should_alert(analysis)
            
            analyses.append(analysis)
        
        # Ordenar por viral_score
        analyses.sort(key=lambda x: x.viral_score, reverse=True)
        
        logger.info(f"📊 Analisados {len(analyses)} sons")
        exploding = [a for a in analyses if a.status == "exploding"]
        if exploding:
            logger.info(f"🔥 {len(exploding)} sons EXPLODINDO!")
        
        return analyses
    
    def _index_history(self, history: List[Dict]) -> Dict[int, List[Dict]]:
        """Indexa histórico por horas atrás"""
        indexed = {}
        now = datetime.now()
        
        for snapshot in history:
            try:
                ts = datetime.fromisoformat(snapshot["timestamp"])
                hours_ago = int((now - ts).total_seconds() / 3600)
                if hours_ago not in indexed:
                    indexed[hours_ago] = []
                indexed[hours_ago].extend(snapshot.get("sounds", []))
            except:
                continue
                
        return indexed
    
    def _calculate_growth(
        self, 
        current: Dict, 
        history: Dict[int, List[Dict]], 
        hours: int
    ) -> float:
        """Calcula crescimento em relação a X horas atrás"""
        title = current.get("title", "")
        current_usage = current.get("usage_count", 0)
        
        if current_usage == 0:
            return 0.0
        
        # Buscar uso anterior (aproximado)
        for h in range(hours - 1, hours + 2):  # Janela de tolerância
            if h in history:
                for old_sound in history[h]:
                    if old_sound.get("title") == title:
                        old_usage = old_sound.get("usage_count", 0)
                        if old_usage > 0:
                            growth = ((current_usage - old_usage) / old_usage) * 100
                            return min(500, max(-100, growth))  # Cap em ±500%
        
        # Sem histórico = som novo (potencialmente interessante)
        return 30.0  # Score base para novos
    
    def _calculate_viral_score(self, analysis: SoundAnalysis) -> float:
        """Calcula score composto de viralidade (0-100)"""
        
        # Normalizar crescimentos para 0-100
        g1h = min(100, max(0, analysis.growth_1h))
        g6h = min(100, max(0, analysis.growth_6h / 2))  # 200% em 6h = 100 score
        g24h = min(100, max(0, analysis.growth_24h / 5))  # 500% em 24h = 100 score
        
        # Bônus de ranking
        rank_bonus = max(0, 100 - (analysis.current_rank * 3))
        
        # Score final
        score = (
            g1h * self.WEIGHTS["growth_1h"] +
            g6h * self.WEIGHTS["growth_6h"] +
            g24h * self.WEIGHTS["growth_24h"] +
            rank_bonus * self.WEIGHTS["rank_bonus"]
        )
        
        return min(100, max(0, score))
    
    def _classify_status(self, viral_score: float) -> str:
        """Classifica status baseado no score"""
        if viral_score >= self.EXPLODING_THRESHOLD:
            return "exploding"
        elif viral_score >= self.RISING_THRESHOLD:
            return "rising"
        return "normal"
    
    def _should_alert(self, analysis: SoundAnalysis) -> bool:
        """Verifica se deve disparar alerta (evita duplicatas)"""
        if analysis.status != "exploding":
            return False
            
        alert_key = f"{analysis.sound_id}_{datetime.now().strftime('%Y%m%d')}"
        
        if alert_key in self._alerts_sent:
            return False
            
        self._alerts_sent.add(alert_key)
        return True
    
    def get_breakout_sounds(
        self, 
        analyses: List[SoundAnalysis],
        threshold: float = 80.0
    ) -> List[SoundAnalysis]:
        """Retorna sons com viral_score acima do threshold"""
        return [a for a in analyses if a.viral_score >= threshold]
    
    def get_sounds_by_status(
        self, 
        analyses: List[SoundAnalysis],
        status: str
    ) -> List[SoundAnalysis]:
        """Filtra por status (exploding, rising, normal)"""
        return [a for a in analyses if a.status == status]
    
    def save_analysis(self, analyses: List[SoundAnalysis]):
        """Salva análises em arquivo"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "analyses": [a.to_dict() for a in analyses]
            }
            with open(ANALYSIS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar análise: {e}")
    
    def load_analysis(self) -> List[SoundAnalysis]:
        """Carrega última análise salva"""
        try:
            if os.path.exists(ANALYSIS_FILE):
                with open(ANALYSIS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [SoundAnalysis(**a) for a in data.get("analyses", [])]
        except Exception as e:
            logger.warning(f"Erro ao carregar análise: {e}")
        return []


# Singleton
viral_analyzer = ViralAnalyzer()
