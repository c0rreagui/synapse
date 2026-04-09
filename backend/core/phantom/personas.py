"""
Phantom Personas — Gen Z behavioral profiles.

Each persona defines:
    - Content preferences (niches, content types)
    - Engagement style (lurker vs. reactor vs. creator)
    - Temporal patterns (peak hours, session duration, frequency)
    - Communication style (comment tone, emoji usage, slang level)
    - Platform quirks (dark mode, screenshot habits, duet preference)

Personas are templates. Individual profiles can apply custom_overrides
via PhantomPersonaAssignment.custom_overrides to fine-tune any field.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


@dataclass
class GenZPersona:
    """Immutable behavioral template for a Gen Z user archetype."""

    # Identity
    name: str
    description: str

    # Content preferences
    primary_niches: List[str]
    secondary_niches: List[str]
    content_ratio: Dict[str, float]  # {"consume": 0.75, "social": 0.15, "explore": 0.10}

    # Engagement
    engagement_style: str  # "lurker" | "reactor" | "socializer" | "creator"
    like_probability: float  # Probability of liking a watched video (0.0-1.0)
    comment_probability: float  # Probability of commenting on a liked video
    save_probability: float  # Probability of saving/bookmarking

    # Timing
    peak_hours: List[int]  # Hours of day with highest activity probability
    avg_daily_sessions: int
    avg_session_minutes: float
    weekend_boost: float  # Multiplier for weekend usage (1.0 = same as weekday)

    # Social
    comment_style: str  # "emoji_heavy" | "slang" | "wholesome" | "chaotic"
    follow_back_rate: float
    max_follows_per_day: int
    max_unfollows_per_day: int

    # Gen Z quirks
    uses_dark_mode: bool = True
    screenshot_rate: float = 0.02
    duet_preference: float = 0.05
    share_rate: float = 0.02

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Persona Library ────────────────────────────────────────────────────────

PERSONAS: Dict[str, GenZPersona] = {

    "aesthetic_curator": GenZPersona(
        name="Aesthetic Curator",
        description="Curates aesthetic content, saves everything, rarely comments. Fashion-forward, design-obsessed.",
        primary_niches=["fashion", "aesthetic", "interior_design", "art"],
        secondary_niches=["cooking", "travel", "skincare"],
        content_ratio={"consume": 0.80, "social": 0.12, "explore": 0.08},
        engagement_style="lurker",
        like_probability=0.18,
        comment_probability=0.04,
        save_probability=0.08,
        peak_hours=[11, 12, 19, 20, 21],
        avg_daily_sessions=5,
        avg_session_minutes=20,
        weekend_boost=1.3,
        comment_style="wholesome",
        follow_back_rate=0.05,
        max_follows_per_day=5,
        max_unfollows_per_day=2,
        screenshot_rate=0.06,
        duet_preference=0.02,
    ),

    "meme_agent": GenZPersona(
        name="Meme Chaos Agent",
        description="Lives for memes and unhinged content. Comments are chaotic. Shares everything to group chats.",
        primary_niches=["comedy", "memes", "commentary", "drama"],
        secondary_niches=["gaming", "music", "true_crime"],
        content_ratio={"consume": 0.65, "social": 0.22, "explore": 0.13},
        engagement_style="reactor",
        like_probability=0.22,
        comment_probability=0.12,
        save_probability=0.03,
        peak_hours=[13, 14, 20, 21, 22, 23],
        avg_daily_sessions=7,
        avg_session_minutes=25,
        weekend_boost=1.5,
        comment_style="chaotic",
        follow_back_rate=0.15,
        max_follows_per_day=8,
        max_unfollows_per_day=3,
        share_rate=0.06,
        duet_preference=0.10,
    ),

    "study_tok": GenZPersona(
        name="StudyTok Scholar",
        description="Productivity and self-improvement focused. Saves tutorials, follows educators. Structured usage.",
        primary_niches=["education", "productivity", "study_tips", "career"],
        secondary_niches=["self_improvement", "aesthetic", "book_tok"],
        content_ratio={"consume": 0.72, "social": 0.16, "explore": 0.12},
        engagement_style="socializer",
        like_probability=0.15,
        comment_probability=0.08,
        save_probability=0.12,
        peak_hours=[8, 9, 14, 15, 20, 21],
        avg_daily_sessions=4,
        avg_session_minutes=15,
        weekend_boost=0.8,  # Less usage on weekends (studious type)
        comment_style="wholesome",
        follow_back_rate=0.20,
        max_follows_per_day=6,
        max_unfollows_per_day=2,
        screenshot_rate=0.08,
    ),

    "music_head": GenZPersona(
        name="Music Discovery Head",
        description="Obsessed with finding new sounds. Heavy use of Sounds page, follows underground artists.",
        primary_niches=["music", "concerts", "underground_artists", "vinyl"],
        secondary_niches=["dance", "fashion", "nightlife"],
        content_ratio={"consume": 0.68, "social": 0.18, "explore": 0.14},
        engagement_style="socializer",
        like_probability=0.20,
        comment_probability=0.10,
        save_probability=0.05,
        peak_hours=[10, 11, 18, 19, 20, 21, 22],
        avg_daily_sessions=6,
        avg_session_minutes=30,
        weekend_boost=1.6,
        comment_style="slang",
        follow_back_rate=0.10,
        max_follows_per_day=10,
        max_unfollows_per_day=4,
        duet_preference=0.15,
    ),

    "brazilian_viral": GenZPersona(
        name="BR Viral Watcher",
        description="Brazilian Gen Z consuming viral cuts, funk, humor, and drama. Heavy emoji user, PT-BR slang.",
        primary_niches=["humor_br", "cortes", "funk", "drama", "fofoca"],
        secondary_niches=["futebol", "comida", "pets", "gringa_react"],
        content_ratio={"consume": 0.72, "social": 0.20, "explore": 0.08},
        engagement_style="reactor",
        like_probability=0.25,
        comment_probability=0.10,
        save_probability=0.03,
        peak_hours=[12, 13, 19, 20, 21, 22, 23],
        avg_daily_sessions=6,
        avg_session_minutes=25,
        weekend_boost=1.4,
        comment_style="emoji_heavy",
        follow_back_rate=0.12,
        max_follows_per_day=8,
        max_unfollows_per_day=3,
        share_rate=0.05,
    ),

    "fitness_girlie": GenZPersona(
        name="Fitness Girlie",
        description="Gym content, healthy recipes, wellness. Structured daily routine, morning-heavy usage.",
        primary_niches=["fitness", "gym", "healthy_eating", "wellness"],
        secondary_niches=["fashion", "motivation", "skincare"],
        content_ratio={"consume": 0.74, "social": 0.16, "explore": 0.10},
        engagement_style="lurker",
        like_probability=0.16,
        comment_probability=0.06,
        save_probability=0.10,
        peak_hours=[6, 7, 12, 13, 20, 21],
        avg_daily_sessions=4,
        avg_session_minutes=18,
        weekend_boost=1.2,
        comment_style="wholesome",
        follow_back_rate=0.08,
        max_follows_per_day=5,
        max_unfollows_per_day=2,
        screenshot_rate=0.05,
    ),
}


def get_persona(key: str) -> Optional[GenZPersona]:
    """Get persona by key. Returns None if not found."""
    return PERSONAS.get(key)


def list_persona_keys() -> List[str]:
    """List all available persona keys."""
    return list(PERSONAS.keys())


def apply_overrides(persona: GenZPersona, overrides: Dict) -> GenZPersona:
    """
    Create a new persona with custom overrides applied.
    Only overrides matching existing fields are applied.
    """
    data = persona.to_dict()
    for key, value in overrides.items():
        if key in data:
            data[key] = value
    return GenZPersona(**data)
