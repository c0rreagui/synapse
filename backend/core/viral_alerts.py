"""
🚨 Viral Alerts - Sistema de Alertas para Sons Explodindo
Notificações em tempo real quando áudios têm crescimento acelerado
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Callable, Set
from dataclasses import dataclass, asdict, field
import json
import os

logger = logging.getLogger(__name__)

DATA_DIR = "data/viral_sounds"
ALERTS_FILE = f"{DATA_DIR}/alerts.json"
PREFERENCES_FILE = f"{DATA_DIR}/alert_preferences.json"


@dataclass
class ViralAlert:
    """Alerta de som viral"""
    id: str
    sound_id: str
    sound_title: str
    sound_author: str
    alert_type: str  # exploding, rising, new_trend, niche_match
    viral_score: float
    growth_rate: float
    niche: str
    message: str
    created_at: str
    read: bool = False
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AlertPreferences:
    """Preferências de alertas do usuário"""
    enabled: bool = True
    niches: List[str] = field(default_factory=lambda: ["tech", "meme", "dance"])
    min_viral_score: float = 80.0  # Score mínimo para alertar
    min_growth_rate: float = 50.0  # % crescimento mínimo
    alert_types: List[str] = field(default_factory=lambda: ["exploding", "rising", "niche_match"])
    
    def to_dict(self) -> dict:
        return asdict(self)


class ViralAlertsService:
    """
    Sistema de alertas para sons virais.
    Detecta sons explodindo e notifica o usuário.
    """
    
    def __init__(self):
        self._ensure_dirs()
        self._alerts: List[ViralAlert] = []
        self._preferences = AlertPreferences()
        self._subscribers: Set[Callable] = set()
        self._last_check = datetime.now()
        self._load_data()
    
    def _ensure_dirs(self):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def _load_data(self):
        """Carrega alertas e preferências salvos"""
        # Alertas
        try:
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._alerts = [ViralAlert(**a) for a in data.get("alerts", [])]
        except Exception as e:
            logger.warning(f"Erro ao carregar alertas: {e}")
        
        # Preferências
        try:
            if os.path.exists(PREFERENCES_FILE):
                with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._preferences = AlertPreferences(**data)
        except Exception as e:
            logger.warning(f"Erro ao carregar preferências: {e}")
    
    def _save_alerts(self):
        """Salva alertas"""
        try:
            with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "alerts": [a.to_dict() for a in self._alerts[-100:]]  # Manter últimos 100
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar alertas: {e}")
    
    def _save_preferences(self):
        """Salva preferências"""
        try:
            with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._preferences.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar preferências: {e}")
    
    def get_preferences(self) -> AlertPreferences:
        """Retorna preferências atuais"""
        return self._preferences
    
    def update_preferences(
        self,
        enabled: Optional[bool] = None,
        niches: Optional[List[str]] = None,
        min_viral_score: Optional[float] = None,
        min_growth_rate: Optional[float] = None,
        alert_types: Optional[List[str]] = None
    ) -> AlertPreferences:
        """Atualiza preferências de alertas"""
        if enabled is not None:
            self._preferences.enabled = enabled
        if niches is not None:
            self._preferences.niches = niches
        if min_viral_score is not None:
            self._preferences.min_viral_score = min_viral_score
        if min_growth_rate is not None:
            self._preferences.min_growth_rate = min_growth_rate
        if alert_types is not None:
            self._preferences.alert_types = alert_types
        
        self._save_preferences()
        logger.info(f"🔔 Preferências atualizadas: {self._preferences}")
        return self._preferences
    
    def create_alert(
        self,
        sound_id: str,
        sound_title: str,
        sound_author: str,
        alert_type: str,
        viral_score: float,
        growth_rate: float,
        niche: str
    ) -> Optional[ViralAlert]:
        """Cria novo alerta se atender às preferências"""
        if not self._preferences.enabled:
            return None
        
        # Verificar se atende aos critérios
        if viral_score < self._preferences.min_viral_score:
            return None
        if growth_rate < self._preferences.min_growth_rate:
            return None
        if alert_type not in self._preferences.alert_types:
            return None
        
        # Verificar match de nicho (se configurado)
        if alert_type == "niche_match" and niche not in self._preferences.niches:
            return None
        
        # Evitar duplicatas (mesmo som nas últimas 6h)
        cutoff = datetime.now() - timedelta(hours=6)
        for existing in self._alerts:
            if existing.sound_id == sound_id:
                if datetime.fromisoformat(existing.created_at) > cutoff:
                    return None
        
        # Gerar mensagem
        message = self._generate_message(sound_title, sound_author, alert_type, viral_score, growth_rate)
        
        # Criar alerta
        alert = ViralAlert(
            id=f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{sound_id[:8]}",
            sound_id=sound_id,
            sound_title=sound_title,
            sound_author=sound_author,
            alert_type=alert_type,
            viral_score=viral_score,
            growth_rate=growth_rate,
            niche=niche,
            message=message,
            created_at=datetime.now().isoformat()
        )
        
        self._alerts.append(alert)
        self._save_alerts()
        
        # Notificar subscribers
        self._notify_subscribers(alert)
        
        logger.info(f"🚨 Alerta criado: {alert.message}")
        return alert
    
    def _generate_message(
        self,
        title: str,
        author: str,
        alert_type: str,
        viral_score: float,
        growth_rate: float
    ) -> str:
        """Gera mensagem do alerta"""
        if alert_type == "exploding":
            return f"🔥 EXPLODING: \"{title}\" de {author} está explodindo! Score: {viral_score:.0f}, +{growth_rate:.0f}% de crescimento"
        elif alert_type == "rising":
            return f"📈 EM ALTA: \"{title}\" de {author} está crescendo rápido! +{growth_rate:.0f}%"
        elif alert_type == "niche_match":
            return f"🎯 MATCH: \"{title}\" combina com seu nicho e está em alta! Score: {viral_score:.0f}"
        elif alert_type == "new_trend":
            return f"✨ NOVA TREND: \"{title}\" de {author} está surgindo no radar!"
        else:
            return f"🔔 \"{title}\" - Score: {viral_score:.0f}"
    
    def subscribe(self, callback: Callable[[ViralAlert], None]):
        """Inscreve callback para receber alertas"""
        self._subscribers.add(callback)
        logger.info(f"🔔 Novo subscriber registrado. Total: {len(self._subscribers)}")
    
    def unsubscribe(self, callback: Callable):
        """Remove callback"""
        self._subscribers.discard(callback)
    
    def _notify_subscribers(self, alert: ViralAlert):
        """Notifica todos os subscribers"""
        for callback in self._subscribers:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erro ao notificar subscriber: {e}")
    
    def get_alerts(
        self,
        limit: int = 20,
        unread_only: bool = False,
        alert_types: Optional[List[str]] = None
    ) -> List[ViralAlert]:
        """Retorna alertas (mais recentes primeiro)"""
        alerts = self._alerts.copy()
        
        if unread_only:
            alerts = [a for a in alerts if not a.read]
        
        if alert_types:
            alerts = [a for a in alerts if a.alert_type in alert_types]
        
        alerts.sort(key=lambda x: x.created_at, reverse=True)
        return alerts[:limit]
    
    def mark_as_read(self, alert_id: str) -> bool:
        """Marca alerta como lido"""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.read = True
                self._save_alerts()
                return True
        return False
    
    def mark_all_as_read(self):
        """Marca todos os alertas como lidos"""
        for alert in self._alerts:
            alert.read = True
        self._save_alerts()
    
    def get_unread_count(self) -> int:
        """Retorna contagem de não lidos"""
        return len([a for a in self._alerts if not a.read])
    
    async def check_for_alerts(self):
        """Verifica sons atuais e cria alertas se necessário"""
        try:
            from core.viral_sounds_service import viral_sounds_service
            
            sounds = await viral_sounds_service.fetch_trending("General", 30)
            
            for sound in sounds:
                # Criar alertas baseado no status
                if sound.status == "exploding":
                    self.create_alert(
                        sound_id=sound.id,
                        sound_title=sound.title,
                        sound_author=sound.author,
                        alert_type="exploding",
                        viral_score=sound.viral_score,
                        growth_rate=sound.growth_rate,
                        niche=sound.niche
                    )
                elif sound.status == "rising" and sound.niche in self._preferences.niches:
                    self.create_alert(
                        sound_id=sound.id,
                        sound_title=sound.title,
                        sound_author=sound.author,
                        alert_type="niche_match",
                        viral_score=sound.viral_score,
                        growth_rate=sound.growth_rate,
                        niche=sound.niche
                    )
            
            self._last_check = datetime.now()
            logger.info(f"✅ Verificação de alertas concluída")
            
        except Exception as e:
            logger.error(f"Erro na verificação de alertas: {e}")


# Singleton
viral_alerts_service = ViralAlertsService()
