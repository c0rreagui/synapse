"""
🕷️ TikTok Creative Center Scraper
Scrape de sons trending do TikTok Creative Center usando Playwright
"""
import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)

# Configurações
CREATIVE_CENTER_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en"
DATA_DIR = "data/viral_sounds"
CACHE_FILE = f"{DATA_DIR}/trending_cache.json"
HISTORY_FILE = f"{DATA_DIR}/history.json"


@dataclass
class ScrapedSound:
    """Som extraído do TikTok Creative Center"""
    id: str
    title: str
    author: str
    cover_url: str
    usage_count: int
    usage_change: float  # % de mudança (ex: +150%)
    rank: int
    region: str
    category: str
    scraped_at: str
    
    # Campos calculados
    viral_score: float = 0.0
    status: str = "normal"  # normal, rising, exploding
    
    def to_dict(self) -> dict:
        return asdict(self)


class ViralScraper:
    """
    Scraper para TikTok Creative Center.
    Extrai sons trending com métricas de crescimento.
    """
    
    # Regiões suportadas pelo Creative Center
    REGIONS = {
        "BR": "Brazil",
        "US": "United States", 
        "GB": "United Kingdom",
        "ALL": "Worldwide"
    }
    
    # Categorias (baseadas no filtro do Creative Center)
    CATEGORIES = [
        "All", "Pop", "Hip Hop", "Electronic", 
        "R&B", "Rock", "Latin", "Country"
    ]
    
    def __init__(self):
        self._ensure_dirs()
        self._history: List[Dict] = []
        self._load_history()
    
    def _ensure_dirs(self):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def _load_history(self):
        """Carrega histórico de scrapes anteriores para calcular crescimento"""
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao carregar histórico: {e}")
            self._history = []
    
    def _save_history(self, sounds: List[ScrapedSound]):
        """Salva snapshot atual no histórico"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "sounds": [s.to_dict() for s in sounds]
        }
        
        # Manter apenas últimas 48 horas de histórico
        cutoff = datetime.now() - timedelta(hours=48)
        self._history = [
            h for h in self._history 
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]
        self._history.append(snapshot)
        
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
    
    async def scrape_trending(
        self, 
        region: str = "BR",
        category: str = "All",
        limit: int = 30
    ) -> List[ScrapedSound]:
        """
        Faz scrape dos sons trending do TikTok Creative Center.
        
        Args:
            region: Código do país (BR, US, GB, ALL)
            category: Categoria de música
            limit: Número máximo de sons
            
        Returns:
            Lista de ScrapedSound com dados e métricas
        """
        logger.info(f"🕷️ Iniciando scrape: região={region}, categoria={category}")
        
        sounds = []
        
        try:
            from core.browser import launch_browser, close_browser

            p, browser, context, page = await launch_browser(
                headless=True,
                viewport={"width": 1920, "height": 1080},
            )
            
            # Construir URL com filtros
            url = self._build_url(region, category)
            logger.info(f"Navegando para: {url}")
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)  # Esperar carregamento JS
            
            # Extrair dados dos cards de musica
            sounds = await self._extract_sounds(page, region, category, limit)
            
            await close_browser(p, browser)
                
        except Exception as e:
            logger.error(f"❌ Erro no scrape: {e}")
            # Retornar cache em caso de erro
            return self._load_cache()
        
        # Calcular métricas de crescimento
        sounds = self._calculate_growth(sounds)
        
        # Salvar cache e histórico
        self._save_cache(sounds)
        self._save_history(sounds)
        
        logger.info(f"✅ Scrape concluído: {len(sounds)} sons extraídos")
        return sounds
    
    def _build_url(self, region: str, category: str) -> str:
        """Constrói URL do Creative Center com filtros"""
        base = CREATIVE_CENTER_URL
        params = []
        
        if region != "ALL":
            params.append(f"region={region}")
        if category != "All":
            params.append(f"category={category.lower()}")
            
        if params:
            return f"{base}?{'&'.join(params)}"
        return base
    
    async def _extract_sounds(
        self, 
        page: Page, 
        region: str, 
        category: str,
        limit: int
    ) -> List[ScrapedSound]:
        """Extrai dados dos cards de música da página"""
        sounds = []
        
        try:
            # Seletores do Creative Center (podem mudar!)
            # Formato: lista de cards com info de música
            cards = page.locator('[class*="music-card"], [class*="sound-item"], [data-testid*="music"]')
            count = await cards.count()
            
            logger.info(f"📊 Encontrados {count} cards de música")
            
            for i in range(min(count, limit)):
                try:
                    card = cards.nth(i)
                    
                    # Extrair dados do card
                    title = await self._safe_text(card, '[class*="title"], h3, h4')
                    author = await self._safe_text(card, '[class*="author"], [class*="artist"]')
                    usage = await self._safe_text(card, '[class*="usage"], [class*="count"]')
                    change = await self._safe_text(card, '[class*="change"], [class*="trend"]')
                    cover = await self._safe_attr(card, 'img', 'src')
                    
                    # Parse dos números
                    usage_count = self._parse_count(usage)
                    usage_change = self._parse_change(change)
                    
                    # Gerar ID único
                    sound_id = f"sound_{i}_{hash(title + author) % 100000}"
                    
                    sound = ScrapedSound(
                        id=sound_id,
                        title=title or f"Som #{i+1}",
                        author=author or "Desconhecido",
                        cover_url=cover or "",
                        usage_count=usage_count,
                        usage_change=usage_change,
                        rank=i + 1,
                        region=region,
                        category=category,
                        scraped_at=datetime.now().isoformat()
                    )
                    sounds.append(sound)
                    
                except Exception as e:
                    logger.warning(f"Erro ao extrair card {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            
        return sounds
    
    async def _safe_text(self, parent, selector: str) -> Optional[str]:
        """Extrai texto de forma segura"""
        try:
            el = parent.locator(selector).first
            if await el.count() > 0:
                return (await el.text_content() or "").strip()
        except:
            pass
        return None
    
    async def _safe_attr(self, parent, selector: str, attr: str) -> Optional[str]:
        """Extrai atributo de forma segura"""
        try:
            el = parent.locator(selector).first
            if await el.count() > 0:
                return await el.get_attribute(attr)
        except:
            pass
        return None
    
    def _parse_count(self, text: Optional[str]) -> int:
        """Parse de contagem (ex: '15.4M' -> 15400000)"""
        if not text:
            return 0
        try:
            text = text.strip().upper()
            if 'M' in text:
                return int(float(text.replace('M', '').replace(',', '')) * 1_000_000)
            if 'K' in text:
                return int(float(text.replace('K', '').replace(',', '')) * 1_000)
            return int(text.replace(',', ''))
        except:
            return 0
    
    def _parse_change(self, text: Optional[str]) -> float:
        """Parse de variação percentual (ex: '+150%' -> 150.0)"""
        if not text:
            return 0.0
        try:
            text = text.strip().replace('%', '').replace('+', '')
            return float(text)
        except:
            return 0.0
    
    def _calculate_growth(self, sounds: List[ScrapedSound]) -> List[ScrapedSound]:
        """Calcula crescimento baseado no histórico"""
        if not self._history:
            # Primeiro scrape, usar dados do Creative Center
            for s in sounds:
                s.viral_score = min(100, s.usage_change)
                s.status = self._classify_status(s.usage_change)
            return sounds
        
        # Comparar com último snapshot
        last_snapshot = self._history[-1]["sounds"]
        last_by_title = {s["title"]: s for s in last_snapshot}
        
        for sound in sounds:
            prev = last_by_title.get(sound.title)
            if prev:
                # Calcular crescimento real
                if prev["usage_count"] > 0:
                    growth = ((sound.usage_count - prev["usage_count"]) / prev["usage_count"]) * 100
                    sound.usage_change = growth
                    sound.viral_score = self._calculate_viral_score(sound, growth)
            else:
                # Novo som - potencialmente interessante
                sound.viral_score = 60  # Score base para novos
            
            sound.status = self._classify_status(sound.usage_change)
        
        return sounds
    
    def _calculate_viral_score(self, sound: ScrapedSound, growth: float) -> float:
        """Calcula score de viralidade (0-100)"""
        # Fórmula: growth peso 60%, rank peso 40%
        growth_score = min(100, max(0, growth))  # Cap em 100
        rank_score = max(0, 100 - (sound.rank * 3))  # Rank 1 = 97, rank 30 = 10
        
        return (growth_score * 0.6) + (rank_score * 0.4)
    
    def _classify_status(self, change: float) -> str:
        """Classifica status do som"""
        if change >= 100:
            return "exploding"  # 🔥 Explodindo
        elif change >= 50:
            return "rising"  # 📈 Crescendo
        else:
            return "normal"  # ✨ Normal
    
    def _save_cache(self, sounds: List[ScrapedSound]):
        """Salva cache local"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "sounds": [s.to_dict() for s in sounds]
            }
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def _load_cache(self) -> List[ScrapedSound]:
        """Carrega cache em caso de falha no scrape"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [ScrapedSound(**s) for s in data.get("sounds", [])]
        except Exception as e:
            logger.warning(f"Erro ao carregar cache: {e}")
        return []
    
    async def get_breakout_sounds(self, threshold: float = 80.0) -> List[ScrapedSound]:
        """Retorna sons que estão 'explodindo' (alto viral_score)"""
        sounds = await self.scrape_trending()
        return [s for s in sounds if s.viral_score >= threshold]


# Singleton
viral_scraper = ViralScraper()


# Função de teste
async def test_scraper():
    """Testa o scraper"""
    scraper = ViralScraper()
    sounds = await scraper.scrape_trending(region="BR", limit=10)
    
    print(f"\n🎵 {len(sounds)} sons encontrados:\n")
    for s in sounds:
        status_emoji = {"exploding": "🔥", "rising": "📈", "normal": "✨"}.get(s.status, "")
        print(f"  {s.rank}. {s.title} - {s.author}")
        print(f"     {status_emoji} Score: {s.viral_score:.1f} | Uso: {s.usage_count:,} | Change: {s.usage_change:+.1f}%")
        print()


if __name__ == "__main__":
    asyncio.run(test_scraper())
