import os

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

# --- DATABASE ---
DB_PATH = os.path.join(BASE_DIR, "synapse.db")

# --- OTHER GLOBALS ---
DEFAULT_TIMEOUT = 30000
