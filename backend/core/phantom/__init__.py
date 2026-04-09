"""
Phantom Engine — TikTok Trust Score System
==========================================

Simulates authentic Gen Z user behavior on TikTok to build and measure
a composite Trust Score for managed profiles.

Modules:
    - personas: Gen Z persona library with behavioral traits
    - behavioral_model: Session planner that decides WHAT to do and WHEN
    - trust_score: Composite score calculator (5 dimensions, 0-100)
    - comment_engine: Context-aware Gen Z comment generator
    - actions/: Action runners (consumption, social, exploration)

Safety:
    - Phantom is disabled by default (PHANTOM_ENABLED=false)
    - All actions are logged immutably in phantom_actions table
    - Hard caps on daily actions, concurrent sessions, and velocities
    - Requires proxy — never runs on bare VPS IP

Usage:
    from core.phantom import phantom_service
    await phantom_service.run_session(profile_id)
    score = phantom_service.get_trust_score(profile_id)
"""

import os

PHANTOM_ENABLED = os.getenv("PHANTOM_ENABLED", "false").lower() == "true"

__all__ = ["PHANTOM_ENABLED"]
