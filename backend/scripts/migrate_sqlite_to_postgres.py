
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import Base, Profile, ScheduleItem, Audit, Trend, PromptTemplate
from core.database import SQLALCHEMY_DATABASE_URL as PG_URL # This will be PG if env vars set

# Hardcoded SQLite Path (Source)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "synapse.db")
SQLITE_URL = f"sqlite:///{SQLITE_DB_PATH}"

def migrate():
    print("--- STARTING MIGRATION: SQLite -> Postgres ---")
    print(f"Source: {SQLITE_URL}")
    print(f"Target: {PG_URL}")
    
    # 1. Connect to SQLite
    sqlite_engine = create_engine(SQLITE_URL)
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    # 2. Connect to Postgres
    # (Assuming PG_URL is correct from env vars injected by Docker or manually)
    if "sqlite" in PG_URL:
        print("ERROR: Target URL is still SQLite. Are env vars set?")
        return

    pg_engine = create_engine(PG_URL)
    PGSession = sessionmaker(bind=pg_engine)
    pg_session = PGSession()
    
    # 3. Create Tables in Postgres
    print("Creating tables in Postgres...")
    Base.metadata.create_all(bind=pg_engine)
    
    # 4. Migrate Data
    try:
        # Profiles
        profiles = sqlite_session.query(Profile).all()
        print(f"Migrating {len(profiles)} Profiles...")
        for p in profiles:
            pg_session.merge(p) # merge handles existing primary keys
        
        # Schedule Items
        items = sqlite_session.query(ScheduleItem).all()
        print(f"Migrating {len(items)} Schedule Items...")
        for i in items:
            pg_session.merge(i)

        # Audit
        audits = sqlite_session.query(Audit).all()
        print(f"Migrating {len(audits)} Audits...")
        for a in audits:
            pg_session.merge(a)

        # Trends
        trends = sqlite_session.query(Trend).all()
        print(f"Migrating {len(trends)} Trends...")
        for t in trends:
            pg_session.merge(t)

        # PromptTemplate
        prompts = sqlite_session.query(PromptTemplate).all()
        print(f"Migrating {len(prompts)} PromptTemplates...")
        for p in prompts:
            pg_session.merge(p)
            
        pg_session.commit()
        print("--- MIGRATION SUCCESSFUL ---")
        
    except Exception as e:
        print(f"Migration Failed: {e}")
        pg_session.rollback()
    finally:
        sqlite_session.close()
        pg_session.close()

if __name__ == "__main__":
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Old database not found at {SQLITE_DB_PATH}. Nothing to migrate.")
    else:
        migrate()
