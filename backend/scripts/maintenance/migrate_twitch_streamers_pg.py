import os
import sys
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

POSTGRES_USER = os.environ.get("POSTGRES_USER", "synapse")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "synapse_password")
POSTGRES_SERVER = os.environ.get("POSTGRES_SERVER", "localhost")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "synapse_db")

DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
print(f"Connecting to: {DB_URL}")

from sqlalchemy import create_engine, inspect
from core.database import Base
from core.clipper.models import TwitchKnownStreamer, TwitchTarget, ClipJob

def migrate():
    engine = create_engine(DB_URL)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    target_table = "twitch_known_streamers"
    if target_table in existing_tables:
        print(f"Table '{target_table}' already exists.")
        return
        
    print(f"Creating table '{target_table}'...")
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    if target_table in inspector.get_table_names():
        print(f"Success! Table '{target_table}' created.")
    else:
        print(f"Failed to create table '{target_table}'.")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
