"""
🎵 Audio Intelligence API Endpoints
Endpoints transversais para sugestão de música viral e análise de áudio.

Consumido por:
- Upload de vídeo (sugestão automática)
- Agendamento (seleção de música)
- Ingestão (enrichment)
- Oracle (análise de compatibilidade)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter()


# ============== Request/Response Models ==============

class SuggestRequest(BaseModel):
    """Request para sugestão de música"""
    niche: Optional[str] = Field(None, description="Nicho do conteúdo (humor, tech, lifestyle)")
    video_path: Optional[str] = Field(None, description="Caminho do vídeo para análise")
    caption: Optional[str] = Field(None, description="Legenda/descrição do vídeo")
    limit: int = Field(3, ge=1, le=10, description="Número máximo de sugestões")
    prefer_exploding: bool = Field(True, description="Priorizar músicas explodindo")


class SoundSuggestionResponse(BaseModel):
    """Sugestão de música retornada pela IA"""
    sound_id: str
    title: str
    author: str
    viral_score: float
    reason: str
    confidence: float
    preview_url: Optional[str] = None
    cover_url: Optional[str] = None
    niche: str = "general"
    status: str = "normal"
    usage_count: int = 0


class SuggestResponse(BaseModel):
    """Response com lista de sugestões"""
    success: bool
    suggestions: List[SoundSuggestionResponse]
    count: int
    analysis_source: str = "audio_intelligence"


class CompatibilityRequest(BaseModel):
    """Request para análise de compatibilidade"""
    video_path: str = Field(..., description="Caminho do vídeo")
    sound_id: str = Field(..., description="ID do som a analisar")


class CompatibilityResponse(BaseModel):
    """Response da análise de compatibilidade"""
    success: bool
    score: float
    breakdown: dict
    recommendation: str


class TrendingResponse(BaseModel):
    """Response com músicas trending"""
    success: bool
    sounds: List[dict]
    niche: str
    count: int


# ============== Endpoints ==============

@router.post("/suggest", response_model=SuggestResponse)
async def suggest_music(request: SuggestRequest):
    """
    🎵 Sugere músicas virais com base no contexto.
    
    Usa IA para analisar o conteúdo e recomendar as melhores
    músicas virais do momento.
    
    - **niche**: Nicho do conteúdo para melhor match
    - **video_path**: Caminho do vídeo para análise (opcional)
    - **caption**: Descrição para análise semântica (opcional)
    - **limit**: Número de sugestões (1-10)
    - **prefer_exploding**: Priorizar músicas explodindo
    """
    try:
        from core.audio_intelligence import audio_intelligence
        
        suggestions = await audio_intelligence.suggest_music(
            niche=request.niche,
            video_path=request.video_path,
            caption=request.caption,
            limit=request.limit,
            prefer_exploding=request.prefer_exploding
        )
        
        return SuggestResponse(
            success=True,
            suggestions=[SoundSuggestionResponse(**s.to_dict()) for s in suggestions],
            count=len(suggestions)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar sugestões: {str(e)}")


@router.post("/compatibility", response_model=CompatibilityResponse)
async def analyze_compatibility(request: CompatibilityRequest):
    """
    📊 Analisa compatibilidade entre vídeo e música.
    
    Retorna um score de 0-100 indicando quão bem a música
    combina com o vídeo, considerando:
    - Potencial viral da música
    - Alinhamento de nicho
    - Status de tendência
    """
    try:
        from core.audio_intelligence import audio_intelligence
        
        result = await audio_intelligence.analyze_compatibility(
            video_path=request.video_path,
            sound_id=request.sound_id
        )
        
        return CompatibilityResponse(
            success=True,
            score=result.score,
            breakdown=result.breakdown,
            recommendation=result.recommendation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


@router.get("/trending/{niche}", response_model=TrendingResponse)
async def get_trending_by_niche(niche: str, limit: int = 10):
    """
    📈 Retorna músicas trending para um nicho específico.
    
    Nichos suportados:
    - humor, comedy, meme
    - tech, tutorial
    - lifestyle, vlog
    - dance, music
    - sports, fitness
    - general (padrão)
    """
    try:
        from core.audio_intelligence import audio_intelligence
        
        sounds = await audio_intelligence.get_trending_for_niche(
            niche=niche,
            limit=limit
        )
        
        return TrendingResponse(
            success=True,
            sounds=sounds,
            niche=niche,
            count=len(sounds)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar trending: {str(e)}")


@router.get("/quick-suggest")
async def quick_suggest(niche: Optional[str] = None):
    """
    ⚡ Retorna uma única sugestão rápida.
    
    Ideal para uso em pipelines onde apenas uma sugestão é necessária.
    """
    try:
        from core.audio_intelligence import audio_intelligence
        
        suggestion = await audio_intelligence.get_quick_suggestion(niche=niche)
        
        if suggestion:
            return {
                "success": True,
                "suggestion": suggestion
            }
        else:
            return {
                "success": False,
                "message": "Nenhuma sugestão disponível"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
