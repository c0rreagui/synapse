"""
🎵 Audio Intelligence - Sistema Transversal de Música Viral
Módulo central que integra análise de áudio e sugestão de músicas virais
para uso em toda a plataforma Synapse.

Consumers:
- Upload (page.tsx) → sugestão automática após upload
- Scheduler (SchedulingModal) → seleção manual/IA
- Ingestão (pipeline) → enrichment automático
- Oracle → análise de compatibilidade
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SuggestionReason(Enum):
    """Razão pela qual uma música foi sugerida"""
    EXPLODING = "exploding"          # Músicas explodindo agora
    NICHE_MATCH = "niche_match"      # Match com o nicho do conteúdo
    HIGH_VIRAL_SCORE = "high_score"  # Alto score viral
    TRENDING = "trending"            # Trending geral
    CONTENT_MATCH = "content_match"  # Match com o conteúdo do vídeo


@dataclass
class SoundSuggestion:
    """Sugestão de música com metadados de IA"""
    sound_id: str
    title: str
    author: str
    viral_score: float
    reason: SuggestionReason
    confidence: float  # 0.0 - 1.0
    preview_url: Optional[str] = None
    cover_url: Optional[str] = None
    niche: str = "general"
    status: str = "normal"
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "reason": self.reason.value
        }


@dataclass
class CompatibilityScore:
    """Score de compatibilidade entre vídeo e música"""
    score: float  # 0-100
    breakdown: Dict[str, float]  # Detalhamento por critério
    recommendation: str  # Texto explicativo
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class SyncPoint:
    """Ponto ideal para iniciar a música no vídeo"""
    timestamp_ms: int
    beat_aligned: bool
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AudioIntelligence:
    """
    🧠 Motor de Inteligência de Áudio
    
    Centraliza toda lógica de sugestão e análise de músicas virais,
    permitindo consumo consistente em toda a plataforma.
    """
    
    def __init__(self):
        self._viral_service = None
        self._initialized = False
    
    def _get_viral_service(self):
        """Lazy load do viral sounds service"""
        if self._viral_service is None:
            try:
                from core.viral_sounds_service import viral_sounds_service
                self._viral_service = viral_sounds_service
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to load viral_sounds_service: {e}")
                self._viral_service = None
        return self._viral_service
    
    async def suggest_music(
        self,
        niche: Optional[str] = None,
        video_path: Optional[str] = None,
        caption: Optional[str] = None,
        limit: int = 3,
        prefer_exploding: bool = True
    ) -> List[SoundSuggestion]:
        """
        🎵 Sugere músicas virais com base no contexto.
        
        Args:
            niche: Nicho do conteúdo (humor, tech, lifestyle, etc)
            video_path: Caminho do vídeo para análise (opcional)
            caption: Legenda/descrição do vídeo (opcional)
            limit: Número máximo de sugestões
            prefer_exploding: Priorizar músicas explodindo
            
        Returns:
            Lista de SoundSuggestion ordenada por relevância
        """
        service = self._get_viral_service()
        if not service:
            logger.warning("Viral service not available, returning empty suggestions")
            return []
        
        suggestions = []
        
        try:
            # 1. Buscar sons trending para o nicho
            sounds = await service.fetch_trending(
                category="General",
                limit=limit * 3,  # Buscar mais para filtrar
                niche=niche
            )
            
            # 2. Se preferir explodindo, buscar breakout sounds
            if prefer_exploding:
                breakout = service.get_breakout_sounds(threshold=75.0)
                # Priorizar breakout sounds
                for sound in breakout[:limit]:
                    suggestions.append(SoundSuggestion(
                        sound_id=sound.id,
                        title=sound.title,
                        author=sound.author,
                        viral_score=sound.viral_score,
                        reason=SuggestionReason.EXPLODING,
                        confidence=0.95,
                        preview_url=sound.preview_url,
                        cover_url=sound.cover_url,
                        niche=sound.niche,
                        status=sound.status,
                        usage_count=sound.usage_count
                    ))
            
            # 3. Adicionar sons por match de nicho
            for sound in sounds:
                if len(suggestions) >= limit:
                    break
                    
                # Evitar duplicatas
                if any(s.sound_id == sound.id for s in suggestions):
                    continue
                
                # Determinar razão e confiança
                if niche and sound.niche.lower() == niche.lower():
                    reason = SuggestionReason.NICHE_MATCH
                    confidence = 0.85
                elif sound.viral_score >= 80:
                    reason = SuggestionReason.HIGH_VIRAL_SCORE
                    confidence = 0.80
                else:
                    reason = SuggestionReason.TRENDING
                    confidence = 0.70
                
                suggestions.append(SoundSuggestion(
                    sound_id=sound.id,
                    title=sound.title,
                    author=sound.author,
                    viral_score=sound.viral_score,
                    reason=reason,
                    confidence=confidence,
                    preview_url=sound.preview_url,
                    cover_url=sound.cover_url,
                    niche=sound.niche,
                    status=sound.status,
                    usage_count=sound.usage_count
                ))
            
            # 4. Ordenar por confiança
            suggestions.sort(key=lambda x: (x.confidence, x.viral_score), reverse=True)
            
            logger.info(f"🎵 Audio Intelligence: Generated {len(suggestions)} suggestions for niche={niche}")
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error generating music suggestions: {e}")
            return []
    
    async def analyze_compatibility(
        self,
        video_path: str,
        sound_id: str
    ) -> CompatibilityScore:
        """
        📊 Analisa compatibilidade entre vídeo e música.
        
        Fatores analisados:
        - Duração compatível
        - Energia/mood match
        - Nicho alignment
        """
        # TODO: Implementar análise real com FFmpeg/librosa
        # Por enquanto, retorna score simulado baseado em heurísticas
        
        service = self._get_viral_service()
        if not service:
            return CompatibilityScore(
                score=50.0,
                breakdown={"availability": 0.0},
                recommendation="Serviço de áudio indisponível"
            )
        
        try:
            # Buscar dados do som
            sounds = await service.fetch_trending(limit=50)
            sound = next((s for s in sounds if s.id == sound_id), None)
            
            if not sound:
                return CompatibilityScore(
                    score=50.0,
                    breakdown={"sound_not_found": 0.0},
                    recommendation="Som não encontrado na biblioteca"
                )
            
            # Calcular scores por critério
            viral_factor = min(sound.viral_score, 100) / 100
            niche_factor = 0.8 if sound.niche != "general" else 0.5
            status_factor = 1.0 if sound.status == "exploding" else 0.7
            
            breakdown = {
                "viral_potential": viral_factor * 100,
                "niche_alignment": niche_factor * 100,
                "trend_status": status_factor * 100
            }
            
            # Score final ponderado
            score = (
                viral_factor * 40 +
                niche_factor * 30 +
                status_factor * 30
            )
            
            # Gerar recomendação
            if score >= 80:
                recommendation = "🟢 Excelente match! Esta música tem alto potencial viral."
            elif score >= 60:
                recommendation = "🟡 Boa escolha. Considere músicas trending para melhor performance."
            else:
                recommendation = "🟠 Match moderado. Recomendamos explorar outras opções."
            
            return CompatibilityScore(
                score=score,
                breakdown=breakdown,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error analyzing compatibility: {e}")
            return CompatibilityScore(
                score=50.0,
                breakdown={"error": str(e)},
                recommendation="Erro na análise"
            )
    
    async def find_sync_point(
        self,
        video_path: str,
        sound_id: str
    ) -> SyncPoint:
        """
        🎯 Encontra o melhor ponto para iniciar a música no vídeo.
        
        Analisa:
        - Beats da música
        - Cortes/transições do vídeo
        - Ênfase visual
        """
        # TODO: Implementar análise real com beat detection
        # Por enquanto, retorna timestamp padrão
        
        return SyncPoint(
            timestamp_ms=0,  # Início do vídeo
            beat_aligned=True,
            confidence=0.75
        )
    
    async def get_trending_for_niche(
        self,
        niche: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        📈 Retorna músicas trending para um nicho específico.
        """
        service = self._get_viral_service()
        if not service:
            return []
        
        try:
            sounds = await service.fetch_trending(
                category="General",
                limit=limit,
                niche=niche
            )
            
            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "author": s.author,
                    "viral_score": s.viral_score,
                    "status": s.status,
                    "niche": s.niche,
                    "preview_url": s.preview_url,
                    "cover_url": s.cover_url
                }
                for s in sounds
            ]
            
        except Exception as e:
            logger.error(f"Error fetching trending for niche {niche}: {e}")
            return []
    
    async def get_quick_suggestion(
        self,
        niche: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ⚡ Retorna uma única sugestão rápida (para uso em pipelines).
        """
        suggestions = await self.suggest_music(niche=niche, limit=1)
        if suggestions:
            return suggestions[0].to_dict()
        return None


# Singleton
audio_intelligence = AudioIntelligence()
