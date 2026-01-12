import logging
import asyncio
from typing import Dict, Optional, List
from playwright.async_api import Page
from core.browser import launch_browser, close_browser

logger = logging.getLogger(__name__)

class OracleCollector:
    """
    The Collector: Eyes of the Oracle.
    Responsible for gathering raw data from external sources (TikTok, etc.)
    using stealth browser automation.
    """
    
    async def collect_tiktok_profile(self, username: str) -> Dict[str, any]:
        """
        Scrapes a TikTok profile for public stats and latest videos.
        """
        logger.info(f"🕵️ OracleCollector: Targeting @{username}...")
        
        p, browser, context, page = await launch_browser(
            headless=True, # TikTok is tough on headless, but let's try.
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        try:
            url = f"https://www.tiktok.com/@{username}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # 1. Basic Identity Check
            # Wait for meaningful content (either followers or video list)
            try:
                await page.wait_for_selector('[data-e2e="user-post-item"]', timeout=10000)
                logger.info("✅ Profile loaded (Video grid detected)")
            except:
                logger.warning("⚠️ Profile might be empty or restricted, checking bio...")

            # 2. Extract Stats (Optimistic selectors)
            stats = {
                "username": username,
                "url": url,
                "followers": "Unknown",
                "following": "Unknown",
                "likes": "Unknown",
                "bio": "",
                "videos": []
            }
            
            # Selectors (TikTok 2024 - these change often)
            selectors = {
                "followers": ['[data-e2e="followers-count"]', 'strong[title="Followers"]'],
                "following": ['[data-e2e="following-count"]', 'strong[title="Following"]'],
                "likes": ['[data-e2e="likes-count"]', 'strong[title="Likes"]'],
                "bio": ['[data-e2e="user-bio"]', '.share-desc']
            }
            
            for key, selector_list in selectors.items():
                for sel in selector_list:
                    if await page.locator(sel).count() > 0:
                        stats[key] = await page.locator(sel).first.inner_text()
                        break
            
            # 3. Extract Latest Videos (Top 5)
            video_elements = await page.locator('[data-e2e="user-post-item"]').all()
            logger.info(f"📹 Found {len(video_elements)} videos")
            
            for i, video in enumerate(video_elements[:5]):
                try:
                    # Title/Desc
                    desc_el = video.locator('div[class*="DivDesDescription"]') # heuristic
                    desc = await desc_el.inner_text() if await desc_el.count() else "No Description"
                    
                    # Views
                    views_el = video.locator('[data-e2e="video-views"]')
                    views = await views_el.inner_text() if await views_el.count() else "0"
                    
                    # Link
                    link_el = video.locator('a')
                    link = await link_el.get_attribute('href') if await link_el.count() else ""
                    
                    stats["videos"].append({
                        "index": i,
                        "description": desc,
                        "views": views,
                        "link": link
                    })
                except Exception as ve:
                    logger.warning(f"Failed to parse video {i}: {ve}")

            return stats

        except Exception as e:
            logger.error(f"❌ Collector failed: {e}")
            return {"error": str(e)}
            
        finally:
            await close_browser(p, browser)

    async def extract_comments(self, video_url: str, max_comments: int = 30) -> List[Dict[str, str]]:
        """
        Scrapes comments from a specific video URL.
        """
        logger.info(f"💬 OracleCollector: Extracting comments from {video_url}...")
        
        # Ensure URL is absolute (TikTok links from scraping might be relative or full)
        if not video_url.startswith('http'):
            video_url = f"https://www.tiktok.com{video_url}"
            
        p, browser, context, page = await launch_browser(headless=True)
        comments = []

        try:
            await page.goto(video_url, wait_until="domcontentloaded", timeout=20000)
            
            # Scroll to load comments
            for _ in range(3):
                await page.keyboard.press("End")
                await asyncio.sleep(1.5)
            
            # Selectors (TikTok 2024 updates)
            # data-e2e="comment-level-1" is the standard container for top-level comments
            comment_items = await page.locator('[data-e2e="comment-level-1"]').all()
            
            for item in comment_items[:max_comments]:
                try:
                    text_el = item.locator('[data-e2e="comment-level-1-content"]')
                    user_el = item.locator('[data-e2e="comment-username"]')
                    
                    if await text_el.count() and await user_el.count():
                        text = await text_el.inner_text()
                        username = await user_el.inner_text()
                        
                        # Basic Bot Filter
                        if len(text) < 3 or text.lower() in ["top", "amei", "lindo", "nice", "wow"]:
                            continue
                            
                        comments.append({"username": username, "text": text})
                except Exception:
                    continue 

            logger.info(f"✅ Extracted {len(comments)} raw comments")
            return comments

        except Exception as e:
            logger.error(f"❌ Comment extraction failed: {e}")
            return []
            
        finally:
            await close_browser(p, browser)

# Singleton instance
oracle_collector = OracleCollector()
