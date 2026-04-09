"""
Phantom Comment Engine — Context-aware Gen Z comment generator.

Generates authentic-sounding comments that match Gen Z communication patterns:
    - Lowercase-dominant, minimal punctuation
    - Strategic emoji usage (never more than 3 in sequence)
    - Current slang with natural abbreviations
    - Context-aware: different styles for different content types
    - Uniqueness: tracks recent comments to avoid repetition

Anti-detection:
    - Never uses bot-flagging patterns (generic praise, links, F4F)
    - Varies comment length and structure
    - Includes occasional natural typos
    - Respects persona-specific communication style
"""

import random
import re
import logging
from collections import deque
from typing import List, Optional, Set
from datetime import datetime

logger = logging.getLogger("PhantomCommentEngine")


# ─── Template Library ────────────────────────────────────────────────────────

TEMPLATES = {
    "reaction_en": [
        "omg this is so {adj} 😂",
        "nahhh 💀💀",
        "the way I just {verb} 😭",
        "this is giving {vibe}",
        "not me watching this {count} times",
        "im screaming 💀",
        "pov: you can't stop rewatching this",
        "bestieee {reaction}",
        "no bc why is this so {adj}",
        "living for this {reaction}",
        "this sent me 💀",
        "okay but {reaction}",
        "LMAOOO {reaction}",
        "why did this show up on my fyp at {time}",
    ],
    "relatable_en": [
        "literally me rn",
        "why is this so accurate 😭",
        "felt this in my soul",
        "ok but why did this call me out",
        "this is the one ✨",
        "the accuracy 💀",
        "ngl this hit different",
        "me every single day",
        "im in this video and I don't like it",
        "pov: literally everyone rn",
    ],
    "question_en": [
        "wait what {object} is that??",
        "link?? 👀",
        "tutorial pls 🙏",
        "how do you do the {thing} part",
        "song name??",
        "where is this 👀",
        "what app is that",
        "need the recipe 🙏",
        "how long did this take",
    ],
    "hype_en": [
        "slay 💅",
        "ate and left no crumbs",
        "mother is mothering",
        "W content fr",
        "this deserves more views",
        "underrated 🔥",
        "obsessed w this",
        "absolutely unhinged and I'm here for it",
        "this is elite",
        "give this person a raise",
    ],
    "reaction_br": [
        "kkkkk mano 😂",
        "n aguento kkkkk 💀",
        "genteee 😭😭",
        "mto bom kkk",
        "esse vídeo é tudo",
        "to passando mal kkkkk",
        "socorro 💀💀",
        "morri com isso",
        "real demais",
        "eu literalmente kkkk",
        "mandou bem dms 🔥",
        "mt isso kk",
        "n consigo parar de assistir",
    ],
    "relatable_br": [
        "literalmente eu",
        "pq isso é tão eu 😭",
        "mds como isso é real",
        "ngm fala sobre isso o suficiente",
        "me senti atacado",
        "todo dia isso kkk",
        "eu todos os dias",
        "nunca me senti tão representado",
    ],
    "hype_br": [
        "arrasou 💅",
        "conteúdo de qualidade",
        "merece mais views",
        "top demais 🔥",
        "simplesmente perfeito",
        "mt talento",
    ],
}

# Emoji pool — weighted by Gen Z usage frequency
EMOJI_POOL = ["😂", "💀", "😭", "✨", "🫶", "💅", "🔥", "👀", "🤌", "💯", "😩", "🥺", "😮‍💨", "🫠", "💜"]
EMOJI_WEIGHTS = [15, 14, 13, 10, 6, 8, 10, 7, 3, 5, 4, 3, 2, 2, 1]

# Slot fillers
ADJECTIVES = ["good", "funny", "real", "accurate", "insane", "perfect", "chaotic", "unhinged", "elite", "wholesome"]
VERBS = ["screamed", "choked", "spit out my drink", "dropped my phone", "lost it", "died", "cried"]
VIBES = ["main character energy", "villain era", "it girl vibes", "chaotic energy", "serotonin", "comfort content"]
REACTIONS = ["😂😂", "💀💀", "😭", "🔥", "✨", "🫶", "💅✨", "😩", "🥺"]
OBJECTS = ["outfit", "filter", "lipstick", "song", "thing in the back", "wallpaper", "plant"]
THINGS = ["transition", "editing", "dance move", "flip thing", "sound sync"]
COUNTS = ["3", "5", "10", "literally 20", "too many"]
TIMES = ["3am", "2am", "midnight", "4am lol"]

# Abbreviations Gen Z uses naturally
ABBREVIATIONS = {
    "to be honest": "tbh",
    "in my opinion": "imo",
    "right now": "rn",
    "not going to lie": "ngl",
    "for real": "fr",
    "I don't know": "idk",
    "to be fair": "tbf",
    "by the way": "btw",
    "in real life": "irl",
    "on my way": "omw",
}

# ─── Forbidden Patterns (instant bot flag) ───────────────────────────────────

FORBIDDEN_PATTERNS = [
    re.compile(r"check out my", re.IGNORECASE),
    re.compile(r"follow for follow", re.IGNORECASE),
    re.compile(r"\bf4f\b", re.IGNORECASE),
    re.compile(r"nice (video|post|content)!", re.IGNORECASE),
    re.compile(r"great (content|video)!", re.IGNORECASE),
    re.compile(r"^amazing!$", re.IGNORECASE),
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"subscribe", re.IGNORECASE),
    re.compile(r"check.*link.*bio", re.IGNORECASE),
]


class CommentEngine:
    """
    Generates contextually appropriate Gen Z comments.

    Tracks recent outputs to enforce uniqueness within a sliding window.
    Uses deque(maxlen) for O(1) append/eviction.
    """

    def __init__(self, uniqueness_window: int = 50):
        self._recent_comments: deque = deque(maxlen=uniqueness_window)
        self._uniqueness_window = uniqueness_window

    def generate(
        self,
        style: str = "reaction",
        language: str = "en",
        niche: Optional[str] = None,
        max_retries: int = 10,
    ) -> str:
        """
        Generate a single comment.

        Args:
            style: "reaction" | "relatable" | "question" | "hype"
            language: "en" | "br"
            niche: Optional content niche for context
            max_retries: Max attempts to generate a unique comment

        Returns:
            Generated comment string.
        """
        template_key = f"{style}_{language}"
        templates = TEMPLATES.get(template_key)

        if not templates:
            # Fallback to reaction in the given language, then English
            templates = TEMPLATES.get(f"reaction_{language}", TEMPLATES["reaction_en"])

        for _ in range(max_retries):
            comment = self._build_comment(templates, language)

            # Check uniqueness
            if comment.lower() not in [c.lower() for c in self._recent_comments]:
                # Check against forbidden patterns
                if not self._is_forbidden(comment):
                    self._track(comment)
                    return comment

        # Exhausted retries — return last generated (still valid, just not unique)
        logger.warning("[COMMENT_ENGINE] Uniqueness window exhausted, returning last attempt")
        self._track(comment)
        return comment

    def generate_batch(
        self,
        count: int,
        style_distribution: Optional[dict] = None,
        language: str = "en",
    ) -> List[str]:
        """
        Generate multiple unique comments with varied styles.

        Args:
            count: Number of comments to generate.
            style_distribution: Optional weights, e.g. {"reaction": 0.5, "relatable": 0.3, "hype": 0.2}
            language: Target language.
        """
        if style_distribution is None:
            style_distribution = {"reaction": 0.40, "relatable": 0.25, "hype": 0.20, "question": 0.15}

        styles = list(style_distribution.keys())
        weights = list(style_distribution.values())

        comments = []
        for _ in range(count):
            style = random.choices(styles, weights=weights, k=1)[0]
            comments.append(self.generate(style=style, language=language))

        return comments

    def _build_comment(self, templates: List[str], language: str) -> str:
        """Build a comment from a random template with slot filling."""
        template = random.choice(templates)

        # Fill slots
        comment = template.format(
            adj=random.choice(ADJECTIVES),
            verb=random.choice(VERBS),
            vibe=random.choice(VIBES),
            reaction=random.choice(REACTIONS),
            object=random.choice(OBJECTS),
            thing=random.choice(THINGS),
            count=random.choice(COUNTS),
            time=random.choice(TIMES),
        )

        # Post-processing
        comment = self._apply_gen_z_style(comment, language)
        return comment

    def _apply_gen_z_style(self, text: str, language: str) -> str:
        """Apply Gen Z writing conventions to the text."""
        # 1. Mostly lowercase (80% of the time)
        if random.random() < 0.80:
            text = text.lower()

        # 2. Remove trailing periods (Gen Z never ends messages with ".")
        text = text.rstrip(".")

        # 3. Maybe add an emoji at the end (30% chance if none present)
        has_emoji = any(c in text for c in "😂💀😭✨🫶💅🔥👀🤌💯😩🥺😮🫠💜")
        if not has_emoji and random.random() < 0.30:
            emoji = random.choices(EMOJI_POOL, weights=EMOJI_WEIGHTS, k=1)[0]
            text = f"{text} {emoji}"

        # 4. Occasional natural typo (3% chance)
        if random.random() < 0.03:
            text = self._inject_typo(text)

        # 5. Trim and ensure length
        text = text.strip()
        if len(text) > 100:
            text = text[:97] + "..."

        return text

    def _inject_typo(self, text: str) -> str:
        """Inject a subtle, natural typo."""
        if len(text) < 5:
            return text

        typo_type = random.choice(["swap", "double", "drop"])
        words = text.split()
        if not words:
            return text

        # Pick a random word (not first, not emoji)
        candidates = [i for i, w in enumerate(words) if len(w) > 3 and not any(c in w for c in "😂💀😭✨🫶💅🔥👀")]
        if not candidates:
            return text

        idx = random.choice(candidates)
        word = words[idx]

        if typo_type == "swap" and len(word) > 3:
            pos = random.randint(1, len(word) - 2)
            word = word[:pos] + word[pos + 1] + word[pos] + word[pos + 2:]
        elif typo_type == "double" and len(word) > 2:
            pos = random.randint(1, len(word) - 1)
            word = word[:pos] + word[pos] + word[pos:]
        elif typo_type == "drop" and len(word) > 4:
            pos = random.randint(1, len(word) - 2)
            word = word[:pos] + word[pos + 1:]

        words[idx] = word
        return " ".join(words)

    def _is_forbidden(self, text: str) -> bool:
        """Check if comment matches any bot-flagging pattern."""
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                logger.debug(f"[COMMENT_ENGINE] Rejected forbidden pattern: {text[:30]}...")
                return True
        return False

    def _track(self, comment: str):
        """Track comment in recent window for uniqueness enforcement."""
        self._recent_comments.append(comment)


# ─── Singleton ───────────────────────────────────────────────────────────────

comment_engine = CommentEngine()
