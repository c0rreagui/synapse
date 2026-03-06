import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import engine, Base
import core.models

def run_migration():
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("Done creating tables.")

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        print("Altering twitch_targets table...")
        
        try:
            conn.execute(text("ALTER TABLE twitch_targets ADD COLUMN target_type VARCHAR DEFAULT 'channel'"))
            print("Column target_type added.")
        except Exception as e:
            print("Column target_type error:", str(e))
            
        try:
            conn.execute(text("ALTER TABLE twitch_targets ADD COLUMN army_id INTEGER REFERENCES armies(id) ON DELETE SET NULL"))
            print("Column army_id added.")
        except Exception as e:
            print("Column army_id error:", str(e))
            
        try:
            conn.execute(text("ALTER TABLE twitch_targets ADD COLUMN category_id VARCHAR"))
            print("Column category_id added.")
        except Exception as e:
            print("Column category_id error:", str(e))
            
        try:
            conn.execute(text("ALTER TABLE twitch_targets DROP COLUMN profile_id"))
            print("Column profile_id dropped.")
        except Exception as e:
            print("Column profile_id already dropped or error:", str(e))
            
        print("Migration complete!")

if __name__ == "__main__":
    run_migration()
