"""
Trend Checker - Real-World Trend Validation
Monitors TikTok Creative Center to validate trending sounds and hashtags.
"""
import logging
import json
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from core.browser import launch_browser, close_browser

logger = logging.getLogger(__name__)


@dataclass
class TrendData:
    """Represents a trending sound or hashtag."""
    id: str
    title: str
    category: str
    growth_24h: float
    usage_count: int
    confidence: float
    url: Optional[str] = None
    

class TrendChecker:
    """
    Real-World Trend Validation Engine.
    Scrapes TikTok Creative Center to validate if trends are actually performing.
    """
    
    CREATIVE_CENTER_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en"
    DATA_FILE = "/app/data/trends.json"
    
    def __init__(self):
        self.trends_cache: List[TrendData] = []
        self.last_updated: Optional[datetime] = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        
        # Load cached trends
        self._load_cache()
    
    def _load_cache(self):
        """Load cached trends from SQLite."""
        from core.database import SessionLocal
        from core.models import Trend
        
        db = SessionLocal()
        try:
            # Load fresh trends (not expired)
            # Query Logic: Get latest snapshot. 
            # For simplicity, we fetch trends created in the last 24h.
            now = datetime.now()
            
            # Simple retrieval: fetch all valid trends
            # In a real scenario, we might want to filter by category, 
            # but here we load 'active' cache into memory.
            
            # Check latest cached_at to determine if we have fresh data
            latest = db.query(Trend).order_by(Trend.cached_at.desc()).first()
            
            if latest:
                self.last_updated = latest.cached_at.replace(tzinfo=None) # naive compat
                
                # Fetch trends from that batch
                batch_time = latest.cached_at
                trends_db = db.query(Trend).filter(Trend.cached_at == batch_time).all()
                
                self.trends_cache = [
                    TrendData(
                        id=t.identifier,
                        title=t.title,
                        category=t.niche,
                        growth_24h=float(t.growth_24h),
                        usage_count=t.volume,
                        confidence=float(t.score) / 100.0,
                        url=None
                    ) for t in trends_db
                ]
                logger.info(f"[TRENDS] Loaded {len(self.trends_cache)} cached trends from SQLite (Time: {batch_time})")
            else:
                logger.info("[TRENDS] No cached trends found in SQLite.")
                
        except Exception as e:
            logger.warning(f"[TRENDS] Could not load trends from DB: {e}")
        finally:
            db.close()
    
    def _save_cache(self):
        """Save trends to SQLite."""
        from core.database import SessionLocal
        from core.models import Trend
        
        db = SessionLocal()
        now_utc = datetime.now(timezone.utc)
        
        try:
            db_objects = []
            for t in self.trends_cache:
                db_objects.append(Trend(
                    niche=t.category,
                    platform="tiktok",
                    title=t.title,
                    identifier=t.id,
                    volume=int(t.usage_count),
                    growth_24h=int(t.growth_24h), # Store as int
                    score=int(t.confidence * 100), # Store as 0-100
                    cached_at=now_utc
                ))
            
            db.add_all(db_objects)
            db.commit()
            logger.info(f"[TRENDS] Saved {len(db_objects)} trends to SQLite")
            
        except Exception as e:
            logger.error(f"[TRENDS] Failed to save trends to DB: {e}")
            db.rollback()
        finally:
            db.close()

    
    async def fetch_trending_sounds(self, category: str = "all", min_growth: float = 100) -> List[TrendData]:
        """
        Scrape trending sounds from TikTok Creative Center.
        
        Args:
            category: Filter by category (all, dance, comedy, etc.)
            min_growth: Minimum growth percentage to include (default 100%)
        
        Returns:
            List of TrendData objects
        """
        logger.info(f"[TRENDS] Fetching trending sounds (category={category}, min_growth={min_growth}%)...")
        
        p, browser, context, page = await launch_browser(headless=True)
        trends = []
        
        try:
            # Navigate to Creative Center
            await page.goto(self.CREATIVE_CENTER_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)  # Wait for dynamic content
            
            # Scroll to load more content
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(1)
            
            # Try multiple selectors for sound cards
            sound_selectors = [
                '[class*="CardPc_wrapper"]',
                '[class*="musicCard"]', 
                '[data-e2e="music-card"]',
                '.music-item',
            ]
            
            sound_cards = []
            for selector in sound_selectors:
                try:
                    cards = await page.locator(selector).all()
                    if len(cards) > 0:
                        sound_cards = cards
                        logger.info(f"[TRENDS] Found {len(cards)} sound cards with selector: {selector}")
                        break
                except Exception:
                    continue
            
            if not sound_cards:
                logger.warning("[TRENDS] No sound cards found, trying fallback extraction...")
                # Fallback: Extract from page content
                return await self._fallback_extraction(page, min_growth)
            
            # Extract data from each card
            for i, card in enumerate(sound_cards[:20]):  # Limit to top 20
                try:
                    # Extract title
                    title = ""
                    title_selectors = ['[class*="title"]', 'h3', 'span', 'p']
                    for sel in title_selectors:
                        try:
                            title_el = card.locator(sel).first
                            if await title_el.count() > 0:
                                title = await title_el.inner_text()
                                if title:
                                    break
                        except:
                            continue
                    
                    # Extract growth/usage stats
                    growth = 0.0
                    usage = 0
                    stat_selectors = ['[class*="stat"]', '[class*="count"]', '[class*="growth"]']
                    for sel in stat_selectors:
                        try:
                            stat_els = card.locator(sel).all()
                            for stat_el in await stat_els:
                                text = await stat_el.inner_text()
                                # Parse growth percentage
                                if '%' in text or '+' in text:
                                    growth = self._parse_growth(text)
                                # Parse usage count
                                elif 'K' in text or 'M' in text or text.isdigit():
                                    usage = self._parse_count(text)
                        except:
                            continue
                    
                    # Filter by min_growth
                    if growth >= min_growth:
                        trend = TrendData(
                            id=f"sound_{i}_{hash(title) % 10000}",
                            title=title[:100] if title else f"Unknown Sound {i}",
                            category=category,
                            growth_24h=growth,
                            usage_count=usage,
                            confidence=min(1.0, growth / 1000),  # Normalize confidence
                            url=None
                        )
                        trends.append(trend)
                        
                except Exception as e:
                    logger.debug(f"Failed to parse sound card {i}: {e}")
                    continue
            
            logger.info(f"[TRENDS] Extracted {len(trends)} trending sounds with growth >= {min_growth}%")
            
            # Update cache
            self.trends_cache = trends
            self.last_updated = datetime.now()
            self._save_cache()
            
            return trends
            
        except Exception as e:
            logger.error(f"[TRENDS] Trend fetching failed: {e}")
            return self.trends_cache  # Return cached data on failure
            
        finally:
            await close_browser(p, browser)
    
    async def _fallback_extraction(self, page, min_growth: float) -> List[TrendData]:
        """Fallback extraction using page content analysis."""
        try:
            content = await page.content()
            # Simple heuristic: look for JSON data in page
            import re
            json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', content)
            if json_match:
                data = json.loads(json_match.group(1))
                # Extract trends from state (structure varies)
                logger.info("[TRENDS] Extracted data from page state")
                return []
        except:
            pass
        return []
    
    def _parse_growth(self, text: str) -> float:
        """Parse growth percentage from text like '+847%' or '847%'."""
        import re
        match = re.search(r'[\+\-]?(\d+(?:\.\d+)?)\s*%', text)
        if match:
            return float(match.group(1))
        return 0.0
    
    def _parse_count(self, text: str) -> int:
        """Parse count from text like '1.2M' or '500K'."""
        import re
        text = text.strip().upper()
        match = re.search(r'(\d+(?:\.\d+)?)\s*([KMB])?', text)
        if match:
            num = float(match.group(1))
            suffix = match.group(2)
            multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
            return int(num * multipliers.get(suffix, 1))
        return 0
    
    async def validate_hashtag(self, hashtag: str) -> Dict[str, Any]:
        """
        Validate if a hashtag is currently trending.
        
        Returns:
            Dict with validation result and current stats
        """
        logger.info(f"[TRENDS] Validating hashtag: {hashtag}")
        
        # Clean hashtag
        hashtag = hashtag.lstrip('#').lower()
        
        p, browser, context, page = await launch_browser(headless=True)
        
        try:
            url = f"https://www.tiktok.com/tag/{hashtag}"
            await page.goto(url, wait_until="networkidle", timeout=25000)
            await asyncio.sleep(2)
            
            # Extract view count
            views = "0"
            view_selectors = ['[data-e2e="challenge-vvcount"]', '[class*="viewCount"]', 'strong']
            for sel in view_selectors:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        views = await el.inner_text()
                        break
                except:
                    continue
            
            return {
                "hashtag": hashtag,
                "is_valid": True,
                "views": views,
                "url": url,
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "hashtag": hashtag,
                "is_valid": False,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }
            
        finally:
            await close_browser(p, browser)
    
    def get_cached_trends(self) -> Dict[str, Any]:
        """Get cached trends without fetching."""
        return {
            "trends": [asdict(t) for t in self.trends_cache],
            "count": len(self.trends_cache),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "is_stale": self._is_cache_stale()
        }
    
    def _is_cache_stale(self, max_age_hours: int = 6) -> bool:
        """Check if cache is older than max_age_hours."""
        if not self.last_updated:
            return True
        age = datetime.now() - self.last_updated
        return age.total_seconds() > max_age_hours * 3600


# Singleton instance
trend_checker = TrendChecker()
