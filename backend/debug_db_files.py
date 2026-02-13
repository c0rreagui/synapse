
import sqlite3
import os
from datetime import datetime

DB_PATH = "sql_app.db"

def check_failed_files():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- FAILED ITEMS ---")
    cursor.execute("SELECT id, profile_slug, status, video_path, scheduled_time, error_message FROM schedule_item WHERE status = 'failed' ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    
    for row in rows:
        item_id, profile, status, path, time, error = row
        exists = os.path.exists(path) if path else False
        print(f"ID: {item_id} | Profile: {profile} | Time: {time}")
        print(f"  Path in DB: {path}")
        print(f"  Exists: {exists}")
        print(f"  Error: {error}")
        
        # If not found, try to find it in other dirs
        if not exists and path:
            filename = os.path.basename(path)
            for d in ["data/pending", "data/approved", "data/processing", "data/errors"]:
                candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), d, filename)
                if os.path.exists(candidate):
                    print(f"  -> FOUND in {d}: {candidate}")

    conn.close()

if __name__ == "__main__":
    check_failed_files()
