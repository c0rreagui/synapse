# Oracle Package - Unified AI Intelligence
from .client import oracle_client
from .oracle import oracle, Oracle
from .faculties import MindFaculty, VisionFaculty, VoiceFaculty, SenseFaculty

# Legacy exports (for backward compatibility during migration)
from .analyst import oracle_analyst
from .seo_engine import seo_engine
from .visual_cortex import visual_cortex
from .collector import oracle_collector

__all__ = [
    "oracle",
    "Oracle",
    "oracle_client",
    "MindFaculty",
    "VisionFaculty", 
    "VoiceFaculty",
    "SenseFaculty",
    # Legacy
    "oracle_analyst",
    "seo_engine",
    "visual_cortex",
    "oracle_collector"
]

