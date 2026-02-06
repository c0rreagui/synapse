"""
Sense Faculty - Data Collection
The senses of the Oracle. Collects data from external sources via stealth scraping.
Migrated from: collector.py
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import Page
from core.browser import launch_browser, close_browser

logger = logging.getLogger(__name__)


class SenseFaculty:
    """
    The Sense: Data Collection Engine.
    Gathers raw data from external sources (TikTok, etc.) using stealth browser automation.
    """

    async def collect_profile(self, username: str, profile_id: Optional[str] = None, timeout: int = 25000) -> Dict[str, Any]:
        """
        Scrapes a TikTok profile for public stats and latest videos.
        Enhanced with authenticated session to bypass bot detection.
        """
        import os
        from core.session_manager import get_session_path, list_available_sessions
        
        logger.info(f"🕵️ Oracle.Sense: Targeting @{username}...")

        # Centralized Paths
        session_path = None
        
        # [NEW] Resolve session dynamically
        if profile_id:
            potential_path = get_session_path(profile_id)
            if os.path.exists(potential_path):
                session_path = potential_path
        else:
            # Try to find a profile in DB that matches this username
            # or just use the first available active session as fallback for stability
            all_sessions = list_available_sessions()
            matching = next((s for s in all_sessions if s.get('username') == username), None)
            if matching:
                session_path = get_session_path(matching['id'])
            elif all_sessions:
                # Fallback to the first healthy session to ensure some level of authentication
                healthy = next((s for s in all_sessions if s.get('session_valid')), None)
                if healthy:
                    session_path = get_session_path(healthy['id'])
        
        if session_path:
             logger.info(f"✅ Using session for scraping: {session_path}")
        else:
            logger.warning("⚠️ No authenticated session resolved, using anonymous mode")
        
        p, browser, context, page = await launch_browser(
            headless=True,
            storage_state=session_path  # Load authenticated cookies if found
        )

        try:
            url = f"https://www.tiktok.com/@{username}"
            await page.goto(url, wait_until="networkidle", timeout=timeout)
            
            # Wait and scroll to trigger lazy loading
            await asyncio.sleep(2)
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(1)
            
            # Try multiple selectors for video grid
            video_selectors = [
                '[data-e2e="user-post-item"]',
                '[class*="DivVideoFeed"] > div',
                '[class*="VideoCard"]',
                'div[class*="item-video"]'
            ]
            
            video_loaded = False
            for selector in video_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        logger.info(f"[SENSE] Profile loaded (Videos found with: {selector})")
                        video_loaded = True
                        break
                except:
                    continue
            
            if not video_loaded:
                logger.warning("[WARNING] Profile might be empty or restricted, checking bio...")

            stats = {
                "username": username,
                "url": url,
                "followers": "Unknown",
                "following": "Unknown",
                "likes": "Unknown",
                "bio": "",
                "videos": [],
                "faculty": "sense"
            }

            from core.ui_selectors import FOLLOWERS_COUNT, FOLLOWING_COUNT, LIKES_COUNT, USER_BIO
            selectors = {
                "followers": [FOLLOWERS_COUNT],
                "following": [FOLLOWING_COUNT],
                "likes": [LIKES_COUNT],
                "bio": [USER_BIO]
            }

            for key, selector_list in selectors.items():
                for sel in selector_list:
                    if await page.locator(sel).count() > 0:
                        stats[key] = await page.locator(sel).first.inner_text()
                        break

            # Avatar Extraction & Fix (Download to avoid 403)
            try:
                from core.ui_selectors import AVATAR_IMG
                avatar_sel = AVATAR_IMG
                if await page.locator(avatar_sel).count() > 0:
                    raw_src = await page.locator(avatar_sel).first.get_attribute("src")
                    if raw_src:
                        import os
                        import aiohttp
                        
                        from core.config import AVATARS_DIR
                        local_filename = f"{username}.jpg"
                        local_path = os.path.join(AVATARS_DIR, local_filename)
                        
                        # Download with centralized headers
                        from core.network_utils import get_scrape_headers
                        async with aiohttp.ClientSession() as session:
                            async with session.get(raw_src, headers=get_scrape_headers()) as resp:
                                if resp.status == 200:
                                    with open(local_path, "wb") as f:
                                        f.write(await resp.read())
                                    # Set stats to LOCAL URL
                                    stats["avatar_url"] = f"http://localhost:8000/static/avatars/{local_filename}"
                                    logger.info(f"[AVATAR] Avatar downloaded: {local_filename}")
                                else:
                                    stats["avatar_url"] = raw_src # Fallback
            except Exception as e:
                logger.warning(f"[WARNING] Avatar download failed: {e}")

            # Scroll more to ensure videos load
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(0.5)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)

            # Try multiple selectors for videos
            video_elements = []
            for selector in video_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if len(elements) > 0:
                        video_elements = elements
                        logger.info(f"[VIDEO] Found {len(video_elements)} videos with selector: {selector}")
                        break
                except:
                    continue
            
            if not video_elements:
                logger.warning("[VIDEO] Found 0 videos with any selector")

            for i, video in enumerate(video_elements[:5]):
                try:
                    from core.ui_selectors import VIDEO_VIEWS
                    # Try multiple view count selectors
                    views = "0"
                    view_selectors = [VIDEO_VIEWS, 'strong', '[class*="Count"]']
                    for v_sel in view_selectors:
                        try:
                            views_el = video.locator(v_sel)
                            if await views_el.count() > 0:
                                views = await views_el.first.inner_text()
                                break
                        except:
                            continue

                    link = ""
                    link_el = video.locator('a')
                    if await link_el.count() > 0:
                        link = await link_el.first.get_attribute('href') or ""

                    stats["videos"].append({
                        "index": i,
                        "views": views,
                        "link": link
                    })
                except Exception as ve:
                    logger.warning(f"Failed to parse video {i}: {ve}")

            return stats

        except Exception as e:
            logger.error(f"[ERROR] Oracle.Sense failed: {e}")
            return {"error": str(e)}

        finally:
            await close_browser(p, browser)

    async def collect_comments(self, video_url: str, max_comments: int = 30) -> List[Dict[str, str]]:
        """
        Scrapes comments from a specific video URL.
        """
        logger.info(f"💬 Oracle.Sense: Extracting comments from {video_url}...")

        if not video_url.startswith('http'):
            video_url = f"https://www.tiktok.com{video_url}"

        p, browser, context, page = await launch_browser(headless=True)
        comments = []

        try:
            await page.goto(video_url, wait_until="domcontentloaded", timeout=20000)

            for _ in range(3):
                await page.keyboard.press("End")
                await asyncio.sleep(1.5)

            from core.ui_selectors import COMMENT_ITEM, COMMENT_CONTENT, COMMENT_USERNAME
            comment_items = await page.locator(COMMENT_ITEM).all()

            for item in comment_items[:max_comments]:
                try:
                    text_el = item.locator(COMMENT_CONTENT)
                    user_el = item.locator(COMMENT_USERNAME)

                    if await text_el.count() and await user_el.count():
                        text = await text_el.inner_text()
                        username = await user_el.inner_text()

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

    async def capture_profile_screenshot(self, username: str) -> str:
        """
        Captures a full-page screenshot of the profile for Visual Audit.
        """
        logger.info(f"📸 Oracle.Sense: Capturing screenshot for @{username}...")
        
        from core.config import SCREENSHOTS_DIR
        filename = f"{username}_audit.png"
        path = os.path.join(SCREENSHOTS_DIR, filename)

        from core.network_utils import get_random_user_agent
        p, browser, context, page = await launch_browser(
            headless=True,
            user_agent=get_random_user_agent()
        )

        try:
            url = f"https://www.tiktok.com/@{username}"
            await page.set_viewport_size({"width": 1280, "height": 800})
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Try to start video or wait a bit for layout to settle
            await asyncio.sleep(2)
            
            # Full Page Screenshot
            # Note: TikTok might lazy load, so maybe just viewport or scroll a bit?
            # Let's scroll once
            await page.evaluate("window.scrollTo(0, 500)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)

            # Capture
            await page.screenshot(path=path, full_page=False) # Viewport is usually enough for "Above the Fold" branding
            
            logger.info(f"✅ Screenshot saved: {path}")
            return path
            
        except Exception as e:
            logger.error(f"❌ Screenshot failed: {e}")
            return ""
            
        finally:
            await close_browser(p, browser)

    async def spy_competitor(self, target_username: str) -> Dict[str, Any]:
        """
        Deep spy on a competitor profile.
        """
        profile_data = await self.collect_profile(target_username)

        if "error" in profile_data:
            return profile_data

        # Collect comments from top video if available
        if profile_data.get("videos"):
            top_video = profile_data["videos"][0]
            if top_video.get("link"):
                comments = await self.collect_comments(top_video["link"])
                profile_data["top_video_comments"] = comments

        profile_data["spy_mode"] = True
        return profile_data
