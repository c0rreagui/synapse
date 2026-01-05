import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Synapse"
    PROJECT_VERSION: str = "0.1.0"
    
    OPUS_CLIP_API_KEY: str = os.getenv("OPUS_CLIP_API_KEY", "")
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

    # Storage
    MEDIA_ROOT: str = os.path.join(os.getcwd(), "media")
    INGEST_DIR: str = os.path.join(MEDIA_ROOT, "ingest")
    READY_DIR: str = os.path.join(MEDIA_ROOT, "ready")

settings = Settings()

# Ensure directories exist
os.makedirs(settings.INGEST_DIR, exist_ok=True)
os.makedirs(settings.READY_DIR, exist_ok=True)
