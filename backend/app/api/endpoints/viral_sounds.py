"""
🎵 Viral Sounds API Endpoints
Endpoints para buscar músicas virais do TikTok com IA
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from core.viral_sounds_service import viral_sounds_service, ViralSound

router = APIRouter()


class ViralSoundResponse(BaseModel):
    """Modelo de resposta para um som viral"""
    id: str
    title: str
    author: str
    cover_url: str
    preview_url: str
    duration: int
    usage_count: int
    category: str
    # Novos campos para IA
    viral_score: float = 0.0
    status: str = "normal"  # normal, rising, exploding
    niche: str = "general"
    growth_rate: float = 0.0
    
    class Config:
        from_attributes = True


class TrendingSoundsResponse(BaseModel):
    """Resposta da listagem de sons trending"""
    sounds: List[ViralSoundResponse]
    category: str
    total: int
    source: str = "cache"  # cache, scraper, mock


class BreakoutSoundsResponse(BaseModel):
    """Resposta de sons explodindo"""
    sounds: List[ViralSoundResponse]
    threshold: float
    total: int
    alert_message: str = ""


@router.get("/trending", response_model=TrendingSoundsResponse)
async def get_trending_sounds(
    category: str = Query(default="General", description="Categoria de sons (General, Dance, Tech, Meme, Lipsync)"),
    niche: Optional[str] = Query(default=None, description="Filtrar por nicho (tech, fitness, meme, dance, etc.)"),
    limit: int = Query(default=20, ge=1, le=50, description="Número máximo de resultados")
):
    """
    🎵 Retorna lista de sons trending do TikTok
    
    Categorias disponíveis:
    - **General**: Trending geral
    - **Dance**: Músicas para danças e challenges
    - **Tech**: Trilhas sonoras tecnológicas
    - **Meme**: Sons de memes e comédia
    - **Lipsync**: Músicas para lip sync
    
    Nichos disponíveis (filtro opcional):
    - tech, fitness, meme, dance, lifestyle, beauty, food, gaming, etc.
    """
    try:
        sounds = await viral_sounds_service.fetch_trending(category, limit)
        
        # Converter para response com campos padrão
        sound_responses = []
        for s in sounds:
            data = s.to_dict()
            # Adicionar campos padrão se não existirem
            data.setdefault("viral_score", 50.0)
            data.setdefault("status", "normal")
            data.setdefault("niche", "general")
            data.setdefault("growth_rate", 0.0)
            sound_responses.append(ViralSoundResponse(**data))
        
        # Filtrar por nicho se especificado
        if niche:
            sound_responses = [s for s in sound_responses if s.niche == niche.lower()]
        
        return TrendingSoundsResponse(
            sounds=sound_responses[:limit],
            category=category,
            total=len(sound_responses),
            source="mock"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar sons: {str(e)}")


@router.get("/breakout", response_model=BreakoutSoundsResponse)
async def get_breakout_sounds(
    threshold: float = Query(default=80.0, ge=0, le=100, description="Score mínimo de viralidade (0-100)"),
    limit: int = Query(default=10, ge=1, le=30, description="Número máximo de resultados")
):
    """
    🔥 Retorna sons que estão EXPLODINDO agora
    
    Sons com viral_score >= threshold são considerados "breakout".
    Score é baseado em crescimento recente (1h, 6h, 24h).
    
    Status dos sons:
    - 🔥 **exploding**: viral_score >= 85
    - 📈 **rising**: viral_score 60-85
    - ✨ **normal**: viral_score < 60
    """
    try:
        # Por enquanto, simular alguns sons breakout
        # TODO: Integrar com viral_scraper e viral_analyzer
        sounds = await viral_sounds_service.fetch_trending("General", 20)
        
        # Simular scores para demo
        breakout_sounds = []
        for i, s in enumerate(sounds):
            data = s.to_dict()
            # Simular viral_score decrescente
            score = max(0, 95 - (i * 10))  # 95, 85, 75, 65...
            data["viral_score"] = score
            data["status"] = "exploding" if score >= 85 else ("rising" if score >= 60 else "normal")
            data["niche"] = "general"
            data["growth_rate"] = score * 1.5  # Simular % de crescimento
            
            if score >= threshold:
                breakout_sounds.append(ViralSoundResponse(**data))
        
        alert_msg = ""
        if breakout_sounds:
            alert_msg = f"🔥 {len(breakout_sounds)} sons explodindo! O mais quente: {breakout_sounds[0].title}"
        
        return BreakoutSoundsResponse(
            sounds=breakout_sounds[:limit],
            threshold=threshold,
            total=len(breakout_sounds),
            alert_message=alert_msg
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar breakout: {str(e)}")


@router.get("/search", response_model=TrendingSoundsResponse)
async def search_sounds(
    query: str = Query(..., min_length=1, description="Termo de busca (título ou artista)"),
    limit: int = Query(default=20, ge=1, le=50, description="Número máximo de resultados")
):
    """
    🔍 Busca sons por nome ou artista
    """
    try:
        sounds = await viral_sounds_service.search(query, limit)
        sound_responses = []
        for s in sounds:
            data = s.to_dict()
            data.setdefault("viral_score", 50.0)
            data.setdefault("status", "normal")
            data.setdefault("niche", "general")
            data.setdefault("growth_rate", 0.0)
            sound_responses.append(ViralSoundResponse(**data))
        
        return TrendingSoundsResponse(
            sounds=sound_responses,
            category="search",
            total=len(sound_responses),
            source="cache"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@router.get("/preview/{sound_id}")
async def get_sound_preview(sound_id: str):
    """
    🎧 Retorna URL de preview para um som específico
    """
    preview_url = viral_sounds_service.get_preview_url(sound_id)
    
    if not preview_url:
        raise HTTPException(status_code=404, detail="Som não encontrado")
    
    return {"sound_id": sound_id, "preview_url": preview_url}


@router.get("/categories")
async def get_categories():
    """
    📂 Retorna lista de categorias disponíveis
    """
    return {
        "categories": list(viral_sounds_service.CATEGORIES.keys()),
        "mapping": viral_sounds_service.CATEGORIES
    }


@router.get("/niches")
async def get_niches():
    """
    🏷️ Retorna lista de nichos disponíveis para filtro
    """
    try:
        from core.niche_classifier import niche_classifier
        return {
            "niches": niche_classifier.get_available_niches(),
            "description": {
                "tech": "Tecnologia, IA, programação",
                "fitness": "Academia, exercícios, saúde",
                "meme": "Humor, comédia, trends",
                "dance": "Danças, challenges",
                "lifestyle": "Dia a dia, rotina, vlogs",
                "beauty": "Maquiagem, skincare, moda",
                "food": "Culinária, receitas",
                "gaming": "Jogos, streams",
                "education": "Educativo, tutoriais",
                "business": "Negócios, finanças",
                "motivation": "Motivacional, autoajuda",
                "music": "Músicas originais, covers",
                "general": "Conteúdo geral"
            }
        }
    except ImportError:
        return {
            "niches": ["general", "tech", "meme", "dance", "fitness"],
            "description": {}
        }
