"""
Phantom Social Module — Simulates social interactions.

Responsible for:
    - Commenting on videos (using CommentEngine for Gen Z text)
    - Following creators
    - Unfollowing (natural churn after a period)

These are medium-risk actions. They require trust >= 21 (building status).
All interactions use human_interaction helpers.
"""

import random
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from playwright.async_api import Page

from core.human_interaction import human_click, human_type, human_move
from core.phantom.comment_engine import comment_engine
from core.phantom.safety import SAFETY

logger = logging.getLogger("PhantomSocial")


# ─── TikTok Selectors (Social) ──────────────────────────────────────────────

SELECTORS = {
    "like_button": 'span[data-e2e="like-icon"]',
    "comment_button": 'span[data-e2e="comment-icon"]',
    "comment_input": 'div[data-e2e="comment-input"]',
    "comment_post_button": 'div[data-e2e="comment-post"]',
    "follow_button": 'button[data-e2e="follow-button"]',
    "unfollow_button": 'button[data-e2e="follow-button"][class*="Following"]',
    "creator_avatar": 'a[data-e2e="video-author-avatar"]',
    "creator_username": 'a[data-e2e="video-author-uniqueid"]',
}


# ─── Follow Ramp-Up Strategy ────────────────────────────────────────────────

FOLLOW_RAMP = {
    # account_age_range: (min_follows_per_day, max_follows_per_day, unfollow_rate)
    (0, 3):   (1, 2, 0.0),
    (4, 7):   (2, 4, 0.05),
    (8, 14):  (3, 6, 0.10),
    (15, 30): (4, 8, 0.15),
    (31, 999): (3, 10, 0.20),
}


def get_follow_limits(account_age_days: int) -> Dict[str, Any]:
    """Get follow/unfollow limits based on account age."""
    for (low, high), (min_f, max_f, unf_rate) in FOLLOW_RAMP.items():
        if low <= account_age_days <= high:
            return {
                "min_follows": min_f,
                "max_follows": max_f,
                "unfollow_rate": unf_rate,
            }
    return {"min_follows": 3, "max_follows": 10, "unfollow_rate": 0.20}


# ─── Social Action Runners ──────────────────────────────────────────────────

class SocialRunner:
    """
    Executes social interaction actions on TikTok.

    Uses CommentEngine for text generation and human_interaction
    for all browser operations.
    """

    async def like_video(self, page: Page) -> Dict[str, Any]:
        """
        Like the currently visible video.

        Returns:
            Result dict with success status.
        """
        result = {
            "action": "like",
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            like_btn = page.locator(SELECTORS["like_button"]).first
            if await like_btn.is_visible(timeout=3000):
                # Check if already liked (button state)
                is_liked = await like_btn.evaluate(
                    "el => el.closest('[class*=\"active\"]') !== null || el.getAttribute('fill') === 'currentColor'"
                )
                if is_liked:
                    logger.debug("[SOCIAL] Video already liked, skipping")
                    return result

                await human_click(page, like_btn, timeout=3000)
                result["success"] = True
                logger.debug("[SOCIAL] Liked video")
        except Exception as e:
            logger.debug(f"[SOCIAL] Like failed: {e}")

        return result

    async def comment_on_video(
        self,
        page: Page,
        style: str = "reaction",
        language: str = "en",
        niche: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Post a comment on the currently visible video.

        1. Opens comment section
        2. Generates a Gen Z comment via CommentEngine
        3. Types it with human-like timing
        4. Posts with a natural delay

        Args:
            style: Comment style ("reaction", "relatable", "question", "hype")
            language: "en" or "br"
            niche: Optional content niche for context

        Returns:
            Result dict with generated text and success status.
        """
        comment_text = comment_engine.generate(style=style, language=language, niche=niche)

        result = {
            "action": "comment",
            "text": comment_text,
            "style": style,
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Open comment section
            comment_btn = page.locator(SELECTORS["comment_button"]).first
            if not await comment_btn.is_visible(timeout=3000):
                logger.debug("[SOCIAL] Comment button not visible")
                return result

            await human_click(page, comment_btn, timeout=3000)
            await page.wait_for_timeout(random.randint(800, 1500))

            # Find and click comment input
            comment_input = page.locator(SELECTORS["comment_input"]).first
            if not await comment_input.is_visible(timeout=5000):
                logger.debug("[SOCIAL] Comment input not visible")
                return result

            await human_click(page, comment_input, timeout=3000)
            await page.wait_for_timeout(random.randint(300, 700))

            # Type comment with human-like timing
            # Pause before typing (thinking about what to say)
            await page.wait_for_timeout(random.randint(800, 2500))

            await human_type(page, comment_text)

            # Brief pause after typing (reviewing what was typed)
            await page.wait_for_timeout(random.randint(500, 1500))

            # Post comment
            post_btn = page.locator(SELECTORS["comment_post_button"]).first
            if await post_btn.is_visible(timeout=3000):
                await human_click(page, post_btn, timeout=3000)
                result["success"] = True
                logger.info(f"[SOCIAL] Posted comment: {comment_text[:30]}...")
            else:
                # Try pressing Enter as fallback
                await page.keyboard.press("Enter")
                result["success"] = True

            # Wait for comment to appear
            await page.wait_for_timeout(random.randint(1000, 2000))

        except Exception as e:
            logger.warning(f"[SOCIAL] Comment failed: {e}")
            result["error"] = str(e)

        return result

    async def follow_creator(self, page: Page) -> Dict[str, Any]:
        """
        Follow the creator of the currently visible video.

        Checks for the follow button and clicks if available.
        Handles the case where already following.
        """
        result = {
            "action": "follow",
            "success": False,
            "creator_handle": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Get creator handle
            creator_el = page.locator(SELECTORS["creator_username"]).first
            if await creator_el.is_visible(timeout=2000):
                result["creator_handle"] = await creator_el.text_content()

            # Find follow button
            follow_btn = page.locator(SELECTORS["follow_button"]).first
            if not await follow_btn.is_visible(timeout=3000):
                logger.debug("[SOCIAL] Follow button not visible")
                return result

            # Check if already following
            btn_text = await follow_btn.text_content()
            if btn_text and "following" in btn_text.lower():
                logger.debug("[SOCIAL] Already following this creator")
                return result

            # Natural delay before following (user would think about it)
            await page.wait_for_timeout(random.randint(500, 1500))

            await human_click(page, follow_btn, timeout=3000)
            result["success"] = True
            logger.info(f"[SOCIAL] Followed: {result['creator_handle']}")

            # Brief wait after follow
            await page.wait_for_timeout(random.randint(300, 800))

        except Exception as e:
            logger.debug(f"[SOCIAL] Follow failed: {e}")
            result["error"] = str(e)

        return result

    async def unfollow_creator(self, page: Page, username: str) -> Dict[str, Any]:
        """
        Unfollow a specific creator (from the Following tab/profile).

        This should be called from the profile's following list, not from FYP.
        """
        result = {
            "action": "unfollow",
            "creator_handle": username,
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Navigate to the user's profile (if not already there)
            # This assumes we're on the following list or the creator's profile
            unfollow_btn = page.locator(f'button:has-text("Following")').first
            if await unfollow_btn.is_visible(timeout=3000):
                await human_click(page, unfollow_btn, timeout=3000)
                await page.wait_for_timeout(random.randint(500, 1000))

                # Confirm unfollow (TikTok may show confirmation)
                confirm = page.locator('button:has-text("Unfollow")').first
                if await confirm.is_visible(timeout=2000):
                    await human_click(page, confirm, timeout=3000)

                result["success"] = True
                logger.info(f"[SOCIAL] Unfollowed: {username}")

        except Exception as e:
            logger.debug(f"[SOCIAL] Unfollow failed: {e}")
            result["error"] = str(e)

        return result


# ─── Singleton ───────────────────────────────────────────────────────────────

social_runner = SocialRunner()
