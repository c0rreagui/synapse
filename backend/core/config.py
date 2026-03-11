import os
import logging
from dotenv import load_dotenv

load_dotenv()

# --- PATH MANAGEMENT ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
STATIC_DIR = os.path.join(BASE_DIR, "static")
AVATARS_DIR = os.path.join(STATIC_DIR, "avatars")
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "screenshots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Processing Envelopes
APPROVED_DIR = os.path.join(DATA_DIR, "approved")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
DONE_DIR = os.path.join(BASE_DIR, "done")
ERRORS_DIR = os.path.join(BASE_DIR, "errors")

# Create essential directories
for d in [DATA_DIR, SESSIONS_DIR, STATIC_DIR, AVATARS_DIR, SCREENSHOTS_DIR, LOGS_DIR, 
          APPROVED_DIR, PROCESSING_DIR, DONE_DIR, ERRORS_DIR]:
    os.makedirs(d, exist_ok=True)

# --- DATABASE & STORAGE ---
DB_PATH = os.path.join(BASE_DIR, "synapse.db")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}")

# --- OTHER GLOBALS ---
DEFAULT_TIMEOUT = 30000

# [SYN-FIX] FFmpeg Local Path
# Add local 'bin' directory to PATH for FFmpeg/FFprobe
LOCAL_BIN = os.path.join(BASE_DIR, "..", "bin")
if os.path.exists(LOCAL_BIN):
    os.environ["PATH"] += os.pathsep + LOCAL_BIN

# --- NOTIFICATIONS & SAFETY ---
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "") # Empty = Disabled
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")) # Max failures allowed
CIRCUIT_BREAKER_WINDOW = int(os.getenv("CIRCUIT_BREAKER_WINDOW", "3600")) # Time window in seconds (1h)

# --- EXTERNAL API KEYS ---
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")

def validate_environment():
    """Validates that all critical environment variables are present at startup."""
    missing = []
    
    if not TWITCH_CLIENT_ID:
        missing.append("TWITCH_CLIENT_ID")
    if not TWITCH_CLIENT_SECRET:
        missing.append("TWITCH_CLIENT_SECRET")
        
    if missing:
        msg = f"CRITICAL ERROR: Missing required environment variables: {', '.join(missing)}"
        logging.getLogger("Synapse").error(msg)
        print(f"\n{'='*60}\n{msg}\n{'='*60}\n")
        raise RuntimeError(msg)
