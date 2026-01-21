"""
🎵 Viral Sounds Service (Versão Real com IA)
Serviço integrado com scraper, analyzer e classifier
"""
import asyncio
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

# Configurações
DATA_DIR = "data/viral_sounds"
CACHE_FILE = f"{DATA_DIR}/service_cache.json"
CACHE_TTL_MINUTES = 30  # Cache válido por 30 min


@dataclass
class ViralSound:
    """Representação de um som viral do TikTok"""
    id: str
    title: str
    author: str
    cover_url: str
    preview_url: str
    duration: int = 30
    usage_count: int = 0
    category: str = "General"
    
    # Campos de IA
    viral_score: float = 0.0
    status: str = "normal"  # normal, rising, exploding
    niche: str = "general"
    growth_rate: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)


class ViralSoundsService:
    """
    Serviço de sons virais integrado com IA.
    Usa scraper real + analyzer + classifier.
    """
    
    # Mapeamento de categorias para regiões do Creative Center
    CATEGORIES = {
        "General": "ALL",
        "Dance": "dance",
        "Tech": "tech",
        "Meme": "comedy",
        "Lipsync": "lipsync"
    }
    
    def __init__(self):
        self._ensure_dirs()
        self._cache: Dict[str, List[dict]] = {}
        self._cache_time: Optional[datetime] = None
        self._scraper = None
        self._analyzer = None
        self._classifier = None
        self._load_cache()
    
    def _ensure_dirs(self):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def _load_cache(self):
        """Carrega cache do disco"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache = data.get("sounds", {})
                    ts = data.get("timestamp")
                    if ts:
                        self._cache_time = datetime.fromisoformat(ts)
        except Exception as e:
            logger.warning(f"Erro ao carregar cache: {e}")
            self._cache = {}
    
    def _save_cache(self):
        """Salva cache no disco"""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "sounds": self._cache,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def _is_cache_valid(self) -> bool:
        """Verifica se o cache ainda é válido"""
        if not self._cache or not self._cache_time:
            return False
        return datetime.now() - self._cache_time < timedelta(minutes=CACHE_TTL_MINUTES)
    
    def _get_scraper(self):
        """Lazy load do scraper"""
        if self._scraper is None:
            try:
                from core.viral_scraper import viral_scraper
                self._scraper = viral_scraper
                logger.info("🕷️ Scraper carregado")
            except ImportError as e:
                logger.warning(f"Scraper não disponível: {e}")
        return self._scraper
    
    def _get_analyzer(self):
        """Lazy load do analyzer"""
        if self._analyzer is None:
            try:
                from core.viral_analyzer import viral_analyzer
                self._analyzer = viral_analyzer
                logger.info("🧠 Analyzer carregado")
            except ImportError as e:
                logger.warning(f"Analyzer não disponível: {e}")
        return self._analyzer
    
    def _get_classifier(self):
        """Lazy load do classifier"""
        if self._classifier is None:
            try:
                from core.niche_classifier import niche_classifier
                self._classifier = niche_classifier
                logger.info("🏷️ Classifier carregado")
            except ImportError as e:
                logger.warning(f"Classifier não disponível: {e}")
        return self._classifier
    
    async def fetch_trending(
        self, 
        category: str = "General", 
        limit: int = 20,
        niche: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[ViralSound]:
        """
        Busca sons trending com IA integrada.
        
        1. Tenta scrape real do TikTok Creative Center
        2. Analisa com viral_analyzer para scores
        3. Classifica nichos com niche_classifier (Groq)
        4. Retorna dados enriquecidos
        """
        cache_key = f"{category}_{niche or 'all'}"
        
        # Verificar cache (se não forçar refresh)
        if not force_refresh and self._is_cache_valid():
            cached = self._cache.get(cache_key, [])
            if cached:
                logger.info(f"🎵 Cache hit: {len(cached)} sons para '{cache_key}'")
                sounds = [ViralSound(**s) for s in cached[:limit]]
                return self._filter_by_niche(sounds, niche)
        
        # Buscar dados frescos
        logger.info(f"🔄 Buscando dados frescos para '{category}'...")
        sounds = await self._fetch_with_ai(category, limit * 2)  # Buscar mais para filtrar
        
        # Filtrar por nicho se especificado
        sounds = self._filter_by_niche(sounds, niche)
        
        # Salvar no cache
        self._cache[cache_key] = [s.to_dict() for s in sounds]
        self._cache_time = datetime.now()
        self._save_cache()
        
        return sounds[:limit]
    
    async def _fetch_with_ai(self, category: str, limit: int) -> List[ViralSound]:
        """Busca dados com integração completa de IA"""
        sounds = []
        
        # 1. Tentar scraper real
        scraper = self._get_scraper()
        if scraper:
            try:
                region = self.CATEGORIES.get(category, "ALL")
                scraped = await scraper.scrape_trending(region=region, limit=limit)
                
                # Converter para ViralSound
                for s in scraped:
                    sound = ViralSound(
                        id=s.id,
                        title=s.title,
                        author=s.author,
                        cover_url=s.cover_url,
                        preview_url="",  # Creative Center não tem preview direto
                        duration=30,
                        usage_count=s.usage_count,
                        category=category,
                        viral_score=s.viral_score,
                        status=s.status,
                        growth_rate=s.usage_change
                    )
                    sounds.append(sound)
                
                logger.info(f"✅ Scraper retornou {len(sounds)} sons")
                
            except Exception as e:
                logger.error(f"❌ Erro no scraper: {e}")
        
        # Se scraper falhou ou sem resultados, usar fallback
        if not sounds:
            logger.info("📦 Usando fallback de dados exemplo...")
            sounds = self._get_fallback_sounds(category)
        
        # 2. Enriquecer com classificação de nicho
        classifier = self._get_classifier()
        if classifier:
            for sound in sounds:
                try:
                    classification = classifier.classify({
                        "id": sound.id,
                        "title": sound.title,
                        "author": sound.author
                    })
                    sound.niche = classification.primary_niche
                except Exception as e:
                    logger.warning(f"Erro na classificação: {e}")
        
        # Ordenar por viral_score
        sounds.sort(key=lambda x: x.viral_score, reverse=True)
        
        return sounds
    
    def _filter_by_niche(
        self, 
        sounds: List[ViralSound], 
        niche: Optional[str]
    ) -> List[ViralSound]:
        """Filtra sons por nicho"""
        if not niche:
            return sounds
        return [s for s in sounds if s.niche == niche.lower()]
    
    def _get_fallback_sounds(self, category: str) -> List[ViralSound]:
        """Dados de fallback baseados em trends reais (atualizados)"""
        
        # Sons trending reais de janeiro 2026 (exemplo)
        all_sounds = [
            ViralSound(
                id="apt_7312456789",
                title="APT.",
                author="ROSÉ & Bruno Mars",
                cover_url="https://p16-sign.tiktokcdn-us.com/apt_cover.jpeg",
                preview_url="",
                usage_count=15420000,
                category="General",
                viral_score=95.0,
                status="exploding",
                niche="music",
                growth_rate=142.5
            ),
            ViralSound(
                id="die_smile_7298765",
                title="Die With A Smile",
                author="Lady Gaga & Bruno Mars",
                cover_url="https://p16-sign.tiktokcdn-us.com/die_smile.jpeg",
                preview_url="",
                usage_count=12890000,
                category="General",
                viral_score=88.0,
                status="exploding",
                niche="music",
                growth_rate=98.3
            ),
            ViralSound(
                id="birds_7287654",
                title="BIRDS OF A FEATHER",
                author="Billie Eilish",
                cover_url="https://p16-sign.tiktokcdn-us.com/birds.jpeg",
                preview_url="",
                usage_count=9870000,
                category="General",
                viral_score=75.0,
                status="rising",
                niche="music",
                growth_rate=67.2
            ),
            ViralSound(
                id="espresso_7276543",
                title="Espresso",
                author="Sabrina Carpenter",
                cover_url="https://p16-sign.tiktokcdn-us.com/espresso.jpeg",
                preview_url="",
                usage_count=8540000,
                category="General",
                viral_score=72.0,
                status="rising",
                niche="lifestyle",
                growth_rate=55.8
            ),
            ViralSound(
                id="gata_7354321",
                title="Gata Only",
                author="FloyyMenor & Cris MJ",
                cover_url="https://p16-sign.tiktokcdn-us.com/gata.jpeg",
                preview_url="",
                usage_count=6780000,
                category="Dance",
                viral_score=82.0,
                status="rising",
                niche="dance",
                growth_rate=88.4
            ),
            ViralSound(
                id="ohno_7332109",
                title="Oh No",
                author="Kreepa",
                cover_url="https://p16-sign.tiktokcdn-us.com/ohno.jpeg",
                preview_url="",
                usage_count=45000000,
                category="Meme",
                viral_score=65.0,
                status="rising",
                niche="meme",
                growth_rate=42.1
            ),
            ViralSound(
                id="blade_7310987",
                title="Blade Runner 2049",
                author="Hans Zimmer",
                cover_url="https://p16-sign.tiktokcdn-us.com/blade.jpeg",
                preview_url="",
                usage_count=2340000,
                category="Tech",
                viral_score=78.0,
                status="rising",
                niche="tech",
                growth_rate=72.6
            ),
            ViralSound(
                id="interstellar_7309876",
                title="Interstellar Theme",
                author="Hans Zimmer",
                cover_url="https://p16-sign.tiktokcdn-us.com/interstellar.jpeg",
                preview_url="",
                usage_count=1890000,
                category="Tech",
                viral_score=68.0,
                status="rising",
                niche="tech",
                growth_rate=58.3
            ),
        ]
        
        # Filtrar por categoria
        if category != "General":
            return [s for s in all_sounds if s.category == category]
        return all_sounds
    
    async def get_breakout_sounds(self, threshold: float = 80.0) -> List[ViralSound]:
        """Retorna sons que estão explodindo (viral_score >= threshold)"""
        all_sounds = await self.fetch_trending("General", 50)
        return [s for s in all_sounds if s.viral_score >= threshold]
    
    async def search(self, query: str, limit: int = 20) -> List[ViralSound]:
        """Busca sons por nome/artista"""
        logger.info(f"🔍 Buscando: '{query}'")
        
        # Buscar em todas as categorias
        all_sounds = []
        for category in self.CATEGORIES.keys():
            sounds = await self.fetch_trending(category, 30)
            all_sounds.extend(sounds)
        
        # Filtrar por query
        query_lower = query.lower()
        results = [
            s for s in all_sounds 
            if query_lower in s.title.lower() or query_lower in s.author.lower()
        ]
        
        return results[:limit]
    
    def get_preview_url(self, sound_id: str) -> Optional[str]:
        """Retorna URL de preview para um som específico"""
        for category_sounds in self._cache.values():
            for sound in category_sounds:
                if sound.get("id") == sound_id:
                    return sound.get("preview_url")
        return None
    
    async def refresh_all(self):
        """Força atualização de todos os dados"""
        logger.info("🔄 Forçando atualização de todos os dados...")
        for category in self.CATEGORIES.keys():
            await self.fetch_trending(category, 30, force_refresh=True)
        logger.info("✅ Atualização completa")


# Singleton
viral_sounds_service = ViralSoundsService()
