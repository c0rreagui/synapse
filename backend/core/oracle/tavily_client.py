"""
Tavily Client
=============

Cliente para integração com Tavily API para pesquisa web e descoberta de tendências.
Usado pelo Oracle para enriquecer análises com dados externos em tempo real.
"""

import os
import json
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


# API Key do Tavily (pode ser sobrescrita via env)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
TAVILY_API_URL = "https://api.tavily.com"

# Cache simples em memória (1 hora)
_cache: Dict[str, tuple[datetime, Any]] = {}
CACHE_TTL = timedelta(hours=1)


@dataclass
class TavilySearchResult:
    """Um resultado de busca do Tavily"""
    title: str
    url: str
    content: str
    score: float
    published_date: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score,
            "published_date": self.published_date
        }


@dataclass
class TavilySearchResponse:
    """Resposta completa de busca do Tavily"""
    query: str
    results: List[TavilySearchResult] = field(default_factory=list)
    answer: Optional[str] = None
    response_time: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "answer": self.answer,
            "response_time": self.response_time
        }


class TavilyClient:
    """
    Cliente para Tavily Search API.
    
    Uso:
        client = TavilyClient()
        results = await client.search("TikTok trends 2024")
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or TAVILY_API_KEY
        self.base_url = TAVILY_API_URL
        
    async def search(
        self,
        query: str,
        search_depth: str = "basic",  # "basic" (1 credit) or "advanced" (2 credits)
        max_results: int = 5,
        include_answer: bool = True,
        include_raw_content: bool = False,
        topic: str = "general",  # "general" or "news"
        days: Optional[int] = None,  # Filtrar por dias recentes (só para news)
        use_cache: bool = True
    ) -> TavilySearchResponse:
        """
        Realiza uma busca no Tavily.
        
        Args:
            query: Termo de busca
            search_depth: "basic" (1 crédito) ou "advanced" (2 créditos)
            max_results: Máximo de resultados (1-10)
            include_answer: Incluir resposta AI resumida
            topic: "general" ou "news"
            days: Filtrar por dias recentes (apenas para news)
            use_cache: Usar cache (1h TTL)
            
        Returns:
            TavilySearchResponse com resultados
        """
        # Verificar cache
        cache_key = f"{query}:{search_depth}:{max_results}:{topic}"
        if use_cache and cache_key in _cache:
            cached_time, cached_data = _cache[cache_key]
            if datetime.now() - cached_time < CACHE_TTL:
                return cached_data
        
        # Construir payload
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": min(max(1, max_results), 10),
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "topic": topic
        }
        
        if topic == "news" and days:
            payload["days"] = days
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = datetime.now()
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload
                )
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code != 200:
                    print(f"Tavily API Error: {response.status_code} - {response.text}")
                    return TavilySearchResponse(query=query)
                
                data = response.json()
                
                # Parsear resultados
                results = []
                for item in data.get("results", []):
                    results.append(TavilySearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("content", ""),
                        score=item.get("score", 0),
                        published_date=item.get("published_date")
                    ))
                
                result = TavilySearchResponse(
                    query=query,
                    results=results,
                    answer=data.get("answer"),
                    response_time=response_time
                )
                
                # Salvar no cache
                if use_cache:
                    _cache[cache_key] = (datetime.now(), result)
                
                return result
                
        except Exception as e:
            print(f"Tavily search error: {e}")
            return TavilySearchResponse(query=query)
    
    async def search_trends(
        self,
        niche: str,
        platform: str = "TikTok"
    ) -> TavilySearchResponse:
        """
        Busca tendências específicas para um nicho e plataforma.
        
        Args:
            niche: Nicho de conteúdo (ex: "fitness", "tech", "comedy")
            platform: Plataforma alvo (default: TikTok)
            
        Returns:
            TavilySearchResponse com tendências
        """
        query = f"{platform} {niche} trends 2024 viral content ideas"
        return await self.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_answer=True,
            topic="news",
            days=7
        )
    
    async def search_hashtags(
        self,
        topic: str,
        platform: str = "TikTok"
    ) -> List[str]:
        """
        Busca hashtags populares para um tópico.
        
        Args:
            topic: Tópico de interesse
            platform: Plataforma alvo
            
        Returns:
            Lista de hashtags encontradas
        """
        query = f"trending {platform} hashtags {topic} 2024"
        result = await self.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True
        )
        
        # Extrair hashtags do conteúdo
        hashtags = []
        for r in result.results:
            content = r.content.lower()
            # Encontrar padrões de hashtag
            import re
            found = re.findall(r'#\w+', content)
            hashtags.extend(found)
        
        # Também extrair da resposta AI
        if result.answer:
            import re
            found = re.findall(r'#\w+', result.answer.lower())
            hashtags.extend(found)
        
        # Remover duplicatas e retornar
        return list(set(hashtags))[:20]
    
    async def analyze_competitor(
        self,
        competitor_name: str,
        platform: str = "TikTok"
    ) -> Dict[str, Any]:
        """
        Analisa um concorrente usando busca web.
        
        Args:
            competitor_name: Nome/handle do concorrente
            platform: Plataforma
            
        Returns:
            Dados sobre o concorrente
        """
        query = f"{competitor_name} {platform} strategy content analysis"
        result = await self.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )
        
        return {
            "competitor": competitor_name,
            "platform": platform,
            "insights": result.answer,
            "sources": [r.to_dict() for r in result.results],
            "analyzed_at": datetime.now().isoformat()
        }


# Instância singleton
tavily_client = TavilyClient()


# Funções de conveniência
async def search_web(query: str, **kwargs) -> TavilySearchResponse:
    """Wrapper para busca web via Tavily"""
    return await tavily_client.search(query, **kwargs)


async def get_niche_trends(niche: str) -> TavilySearchResponse:
    """Busca tendências para um nicho específico"""
    return await tavily_client.search_trends(niche)


async def get_trending_hashtags(topic: str) -> List[str]:
    """Busca hashtags em alta para um tópico"""
    return await tavily_client.search_hashtags(topic)
