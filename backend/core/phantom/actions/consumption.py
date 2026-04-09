"""
Phantom Consumption Module — Simulates passive content consumption.

Responsible for:
    - FYP scrolling sessions (swipe through videos)
    - Video watching (with bimodal watch-time distribution)
    - Saving/bookmarking content
    - Internal sharing (copy link)

This is the lowest-risk, highest-volume action type.
It uses the existing human_interaction module for all browser interactions.
"""

import random
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from playwright.async_api import Page

from core.human_interaction import human_scroll, human_click, human_move
from core.phantom.safety import SAFETY

logger = logging.getLogger("PhantomConsumption")


# ─── Watch Time Distribution ─────────────────────────────────────────────────

def get_watch_duration_seconds(estimated_video_length: float = 15.0) -> float:
    """
    Calculate how long to watch a video.

    Gen Z watch time follows a bimodal distribution:
        - Peak 1 (~38%): Quick skip at 5-35% of video ("not for me")
        - Peak 2 (~62%): Engaged viewing at 70-115% (might rewatch start)

    Args:
        estimated_video_length: Estimated video length in seconds.

    Returns:
        Watch duration in seconds.
    """
    if random.random() < 0.38:
        # Quick skip
        ratio = random.triangular(0.05, 0.35, 0.15)
    else:
        # Engaged viewing — sometimes rewatches the beginning
        ratio = random.triangular(0.70, 1.15, 0.92)

    return estimated_video_length * ratio


# ─── TikTok Element Selectors ────────────────────────────────────────────────
# These are CSS selectors for TikTok's web interface.
# Updated as needed when TikTok changes their DOM structure.

SELECTORS = {
    "video_player": 'div[data-e2e="browse-video"]',
    "like_button": 'span[data-e2e="like-icon"]',
    "comment_button": 'span[data-e2e="comment-icon"]',
    "share_button": 'span[data-e2e="share-icon"]',
    "save_button": 'span[data-e2e="undefined-icon"]',  # Bookmark icon
    "follow_button": 'button[data-e2e="follow-button"]',
    "video_container": 'div[class*="DivVideoContainer"]',
    "fyp_tab": 'a[data-e2e="nav-foryou"]',
    "following_tab": 'a[data-e2e="nav-following"]',
    "search_input": 'input[data-e2e="search-user-input"]',
    "copy_link_button": 'button[data-e2e="share-copylink"]',
}


# ─── Consumption Action Runners ──────────────────────────────────────────────

class ConsumptionRunner:
    """
    Executes consumption actions on a TikTok page.

    All interactions use human_interaction helpers (Bézier mouse, Gaussian timing)
    to avoid bot detection.
    """

    async def scroll_fyp(
        self,
        page: Page,
        duration_minutes: float,
        like_probability: float = 0.15,
        save_probability: float = 0.03,
    ) -> Dict[str, Any]:
        """
        Simulate a FYP (For You Page) scrolling session.

        Scrolls through videos, watches each one for a natural duration,
        occasionally likes, saves, or just moves on.

        Returns:
            Dict with session metrics (videos_watched, likes, saves, etc.)
        """
        metrics = {
            "videos_watched": 0,
            "total_watch_seconds": 0,
            "likes": 0,
            "saves": 0,
            "skips": 0,
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

        end_time = time.monotonic() + (duration_minutes * 60)

        while time.monotonic() < end_time:
            try:
                # Watch current video
                watch_result = await self._watch_current_video(page)
                metrics["videos_watched"] += 1
                metrics["total_watch_seconds"] += watch_result.get("watch_seconds", 0)

                if watch_result.get("skipped", False):
                    metrics["skips"] += 1
                else:
                    # Maybe like (only if actually watched)
                    if random.random() < like_probability:
                        liked = await self._like_current_video(page)
                        if liked:
                            metrics["likes"] += 1

                    # Maybe save
                    if random.random() < save_probability:
                        saved = await self._save_current_video(page)
                        if saved:
                            metrics["saves"] += 1

                # Scroll to next video
                await self._swipe_to_next(page)

                # Brief pause between videos (human would need a moment)
                await page.wait_for_timeout(random.randint(300, 1200))

            except Exception as e:
                logger.warning(f"[CONSUMPTION] Error during FYP scroll: {e}")
                # Don't crash — just move to next video
                await self._swipe_to_next(page)
                await page.wait_for_timeout(random.randint(1000, 3000))

        metrics["end_time"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"[CONSUMPTION] FYP session: {metrics['videos_watched']} videos, "
                     f"{metrics['likes']} likes, {metrics['saves']} saves")
        return metrics

    async def _watch_current_video(self, page: Page) -> Dict[str, Any]:
        """
        Watch the currently visible video for a natural duration.

        Uses bimodal watch time distribution (quick skip vs. engaged viewing).
        """
        # Estimate video length (TikTok shows duration or we estimate ~15s avg)
        estimated_length = random.uniform(10, 45)  # Most TikToks are 10-45 seconds

        watch_duration = get_watch_duration_seconds(estimated_length)
        is_skip = watch_duration < estimated_length * 0.4

        # Wait for the watch duration (this is the actual "watching")
        await page.wait_for_timeout(int(watch_duration * 1000))

        # During longer watches, simulate occasional mouse micro-movements
        # (real users fidget, move cursor around)
        if not is_skip and watch_duration > 5:
            num_fidgets = random.randint(0, 2)
            for _ in range(num_fidgets):
                fidget_x = random.randint(200, 800)
                fidget_y = random.randint(200, 600)
                await human_move(page, fidget_x, fidget_y, duration_ms=random.randint(100, 300))

        return {
            "watch_seconds": round(watch_duration, 1),
            "estimated_length": estimated_length,
            "watch_pct": round(watch_duration / estimated_length, 2),
            "skipped": is_skip,
        }

    async def _swipe_to_next(self, page: Page):
        """
        Swipe/scroll to the next video in the feed.

        TikTok web uses vertical scrolling (one video per screen).
        """
        # Natural swipe down — one full viewport height
        await human_scroll(page, direction="down", amount=random.randint(600, 900))

        # Wait for video to start loading
        await page.wait_for_timeout(random.randint(200, 600))

    async def _like_current_video(self, page: Page) -> bool:
        """Double-tap or click the like button on the current video."""
        try:
            like_btn = page.locator(SELECTORS["like_button"]).first
            if await like_btn.is_visible(timeout=2000):
                await human_click(page, like_btn, timeout=3000)
                logger.debug("[CONSUMPTION] Liked video")
                return True
        except Exception as e:
            logger.debug(f"[CONSUMPTION] Like failed: {e}")
        return False

    async def _save_current_video(self, page: Page) -> bool:
        """Click the save/bookmark button."""
        try:
            save_btn = page.locator(SELECTORS["save_button"]).first
            if await save_btn.is_visible(timeout=2000):
                await human_click(page, save_btn, timeout=3000)
                logger.debug("[CONSUMPTION] Saved video")
                return True
        except Exception as e:
            logger.debug(f"[CONSUMPTION] Save failed: {e}")
        return False

    async def _copy_link(self, page: Page) -> bool:
        """Share via copy link (internal share)."""
        try:
            share_btn = page.locator(SELECTORS["share_button"]).first
            if await share_btn.is_visible(timeout=2000):
                await human_click(page, share_btn, timeout=3000)
                await page.wait_for_timeout(random.randint(500, 1000))

                copy_btn = page.locator(SELECTORS["copy_link_button"]).first
                if await copy_btn.is_visible(timeout=2000):
                    await human_click(page, copy_btn, timeout=3000)
                    logger.debug("[CONSUMPTION] Copied link")
                    return True
        except Exception as e:
            logger.debug(f"[CONSUMPTION] Copy link failed: {e}")
        return False


# ─── Singleton ───────────────────────────────────────────────────────────────

consumption_runner = ConsumptionRunner()
