"""
Phantom Exploration Module — Simulates organic navigation behavior.

Responsible for:
    - Search (hashtags, sounds, creators, keywords)
    - Discover page browsing
    - Tab navigation (FYP ↔ Following ↔ Discover)
    - Notification checking
    - Profile visits (self and others)

These are low-risk actions that demonstrate curiosity and organic usage patterns.
Absence of exploration behavior is itself a red flag for detection systems.
"""

import random
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from playwright.async_api import Page

from core.human_interaction import human_click, human_type, human_move, human_scroll
from core.phantom.safety import SAFETY

logger = logging.getLogger("PhantomExploration")


# ─── TikTok Selectors (Exploration) ─────────────────────────────────────────

SELECTORS = {
    "search_icon": 'button[data-e2e="search-icon"]',
    "search_input": 'input[data-e2e="search-user-input"]',
    "search_clear": 'span[data-e2e="search-clear"]',
    "fyp_tab": 'a[data-e2e="nav-foryou"]',
    "following_tab": 'a[data-e2e="nav-following"]',
    "discover_tab": 'a[data-e2e="nav-discover"]',
    "inbox_tab": 'a[data-e2e="nav-inbox"]',
    "profile_tab": 'a[data-e2e="nav-profile"]',
    "trending_hashtags": 'a[data-e2e="search-card-tag"]',
    "search_results_video": 'div[data-e2e="search-card-video"]',
    "search_tab_videos": 'a[data-e2e="search-videos-tab"]',
    "search_tab_users": 'a[data-e2e="search-users-tab"]',
    "search_tab_sounds": 'a[data-e2e="search-sounds-tab"]',
    "search_tab_hashtags": 'a[data-e2e="search-hashtags-tab"]',
    "notification_count": 'span[data-e2e="inbox-count"]',
}

# Search query templates by type
SEARCH_QUERIES = {
    "hashtag": [
        "#{niche}",
        "#trending {niche}",
        "#{niche}tok",
        "#{niche} 2026",
        "#best{niche}",
    ],
    "keyword": [
        "{niche} tips",
        "best {niche} content",
        "{niche} tutorial",
        "how to {niche}",
        "{niche} for beginners",
    ],
    "sound": [
        "trending sounds",
        "viral sound {niche}",
        "popular audio",
    ],
    "creator": [
        "{niche} creator",
        "best {niche} tiktoker",
    ],
}


# ─── Exploration Action Runners ──────────────────────────────────────────────

class ExplorationRunner:
    """
    Executes exploration actions on TikTok.

    Simulates the natural curiosity of browsing, searching,
    and navigating different sections of the app.
    """

    async def search(
        self,
        page: Page,
        niche: str,
        query_type: str = "hashtag",
        browse_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform a search on TikTok.

        1. Click search icon
        2. Type query with human-like timing
        3. Browse results for a natural duration
        4. Return to FYP

        Args:
            niche: Content niche to search for.
            query_type: "hashtag" | "keyword" | "sound" | "creator"
            browse_results: Whether to scroll through results.
        """
        result = {
            "action": "search",
            "query_type": query_type,
            "niche": niche,
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Build search query
            templates = SEARCH_QUERIES.get(query_type, SEARCH_QUERIES["keyword"])
            query = random.choice(templates).format(niche=niche)
            result["query"] = query

            # Click search
            search_icon = page.locator(SELECTORS["search_icon"]).first
            if not await search_icon.is_visible(timeout=3000):
                # Try finding search input directly
                search_input = page.locator(SELECTORS["search_input"]).first
                if not await search_input.is_visible(timeout=3000):
                    logger.debug("[EXPLORATION] Search icon/input not visible")
                    return result
            else:
                await human_click(page, search_icon, timeout=3000)
                await page.wait_for_timeout(random.randint(500, 1000))

            # Type search query
            search_input = page.locator(SELECTORS["search_input"]).first
            await human_click(page, search_input, timeout=3000)
            await page.wait_for_timeout(random.randint(300, 700))

            # Clear any existing text
            await page.keyboard.press("Control+a")
            await page.keyboard.press("Backspace")
            await page.wait_for_timeout(random.randint(200, 500))

            # Type query
            await human_type(page, query)
            await page.wait_for_timeout(random.randint(300, 600))

            # Submit search
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(random.randint(1500, 3000))

            result["success"] = True
            logger.info(f"[EXPLORATION] Searched: {query}")

            # Optionally browse results
            if browse_results:
                browse_time = random.uniform(10, 30)  # seconds
                result["browse_seconds"] = round(browse_time, 1)

                # Scroll through results
                scrolls = random.randint(2, 5)
                for _ in range(scrolls):
                    await human_scroll(page, "down", amount=random.randint(300, 600))
                    await page.wait_for_timeout(random.randint(1000, 3000))

                # Maybe click on a search tab
                if random.random() < 0.3:
                    tab_selector = random.choice([
                        SELECTORS["search_tab_videos"],
                        SELECTORS["search_tab_users"],
                        SELECTORS["search_tab_sounds"],
                    ])
                    tab = page.locator(tab_selector).first
                    if await tab.is_visible(timeout=2000):
                        await human_click(page, tab, timeout=3000)
                        await page.wait_for_timeout(random.randint(1000, 2000))

        except Exception as e:
            logger.warning(f"[EXPLORATION] Search failed: {e}")
            result["error"] = str(e)

        return result

    async def navigate_tab(
        self,
        page: Page,
        tabs: List[str],
    ) -> Dict[str, Any]:
        """
        Navigate between TikTok tabs (FYP, Following, Discover).

        Simulates natural tab switching. Real users switch tabs frequently.
        Absence of tab navigation is a red flag.

        Args:
            tabs: List of tab names to navigate through, e.g. ["fyp", "following"]
        """
        result = {
            "action": "tab_navigation",
            "tabs": tabs,
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        tab_map = {
            "fyp": SELECTORS["fyp_tab"],
            "following": SELECTORS["following_tab"],
            "discover": SELECTORS["discover_tab"],
            "inbox": SELECTORS["inbox_tab"],
            "profile": SELECTORS["profile_tab"],
        }

        try:
            for tab_name in tabs:
                selector = tab_map.get(tab_name)
                if not selector:
                    continue

                tab_el = page.locator(selector).first
                if await tab_el.is_visible(timeout=3000):
                    await human_click(page, tab_el, timeout=3000)
                    logger.debug(f"[EXPLORATION] Navigated to {tab_name}")

                    # Pause on tab (natural browsing behavior)
                    await page.wait_for_timeout(random.randint(2000, 5000))

                    # Maybe scroll a bit on the new tab
                    if random.random() < 0.5:
                        await human_scroll(page, "down", amount=random.randint(200, 400))
                        await page.wait_for_timeout(random.randint(1000, 2000))

            result["success"] = True

        except Exception as e:
            logger.debug(f"[EXPLORATION] Tab navigation failed: {e}")
            result["error"] = str(e)

        return result

    async def check_notifications(self, page: Page) -> Dict[str, Any]:
        """
        Check the notifications/inbox tab.

        Real users check notifications regularly. Missing this behavior
        is a subtle but detectable pattern.
        """
        result = {
            "action": "notification_check",
            "success": False,
            "has_notifications": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            inbox_tab = page.locator(SELECTORS["inbox_tab"]).first
            if not await inbox_tab.is_visible(timeout=3000):
                return result

            # Check if there's a notification badge
            badge = page.locator(SELECTORS["notification_count"]).first
            if await badge.is_visible(timeout=1000):
                result["has_notifications"] = True

            await human_click(page, inbox_tab, timeout=3000)
            await page.wait_for_timeout(random.randint(2000, 5000))

            # Scroll through notifications briefly
            if random.random() < 0.6:
                await human_scroll(page, "down", amount=random.randint(200, 500))
                await page.wait_for_timeout(random.randint(1000, 3000))

            result["success"] = True
            logger.debug("[EXPLORATION] Checked notifications")

            # Return to FYP
            fyp_tab = page.locator(SELECTORS["fyp_tab"]).first
            if await fyp_tab.is_visible(timeout=2000):
                await human_click(page, fyp_tab, timeout=3000)

        except Exception as e:
            logger.debug(f"[EXPLORATION] Notification check failed: {e}")
            result["error"] = str(e)

        return result

    async def visit_own_profile(self, page: Page) -> Dict[str, Any]:
        """
        Visit own profile page. Real users check their profile occasionally
        to see follower count, recent uploads, and profile appearance.
        """
        result = {
            "action": "visit_profile",
            "profile_type": "self",
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            profile_tab = page.locator(SELECTORS["profile_tab"]).first
            if await profile_tab.is_visible(timeout=3000):
                await human_click(page, profile_tab, timeout=3000)
                await page.wait_for_timeout(random.randint(3000, 6000))

                # Scroll down to see recent videos
                if random.random() < 0.5:
                    await human_scroll(page, "down", amount=random.randint(200, 500))
                    await page.wait_for_timeout(random.randint(1000, 3000))

                result["success"] = True
                logger.debug("[EXPLORATION] Visited own profile")

                # Return to FYP
                fyp_tab = page.locator(SELECTORS["fyp_tab"]).first
                if await fyp_tab.is_visible(timeout=2000):
                    await human_click(page, fyp_tab, timeout=3000)

        except Exception as e:
            logger.debug(f"[EXPLORATION] Profile visit failed: {e}")
            result["error"] = str(e)

        return result

    async def browse_discover(self, page: Page) -> Dict[str, Any]:
        """
        Browse the Discover/trending page.

        Scrolls through trending hashtags, sounds, and videos.
        """
        result = {
            "action": "browse_discover",
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            discover_tab = page.locator(SELECTORS["discover_tab"]).first
            if not await discover_tab.is_visible(timeout=3000):
                # Discover may not always be visible; some regions show it differently
                logger.debug("[EXPLORATION] Discover tab not visible")
                return result

            await human_click(page, discover_tab, timeout=3000)
            await page.wait_for_timeout(random.randint(2000, 4000))

            # Browse trending content
            browse_time = random.uniform(15, 40)  # seconds
            result["browse_seconds"] = round(browse_time, 1)

            scrolls = random.randint(3, 7)
            for _ in range(scrolls):
                await human_scroll(page, "down", amount=random.randint(300, 600))
                await page.wait_for_timeout(random.randint(1500, 3000))

                # Maybe click on a trending hashtag
                if random.random() < 0.2:
                    trending = page.locator(SELECTORS["trending_hashtags"]).first
                    if await trending.is_visible(timeout=1000):
                        await human_click(page, trending, timeout=3000)
                        await page.wait_for_timeout(random.randint(2000, 5000))
                        await page.go_back()
                        await page.wait_for_timeout(random.randint(1000, 2000))

            result["success"] = True
            logger.debug("[EXPLORATION] Browsed discover page")

            # Return to FYP
            fyp_tab = page.locator(SELECTORS["fyp_tab"]).first
            if await fyp_tab.is_visible(timeout=2000):
                await human_click(page, fyp_tab, timeout=3000)

        except Exception as e:
            logger.debug(f"[EXPLORATION] Discover browsing failed: {e}")
            result["error"] = str(e)

        return result


# ─── Singleton ───────────────────────────────────────────────────────────────

exploration_runner = ExplorationRunner()
