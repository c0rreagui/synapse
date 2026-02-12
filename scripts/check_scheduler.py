import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("backend", "synapse.db")

def check_schedule():
    if not os.path.exists(DB_PATH):
        print(f"No DB found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        if ('schedule',) in tables:
            print("\n--- Status Summary ---")
            cursor.execute("SELECT status, COUNT(*) FROM schedule GROUP BY status")
            summary = cursor.fetchall()
            for status, count in summary:
                print(f"Status '{status}': {count} items")

            print("\n--- First 10 Items (Any Status) ---")
            cursor.execute("SELECT id, profile_slug, scheduled_time, status FROM schedule ORDER BY scheduled_time ASC LIMIT 10")
            rows = cursor.fetchall()
            for row in rows:
                print(f"ID: {row[0]} | Profile: {row[1]} | Time: {row[2]} | Status: {row[3]}")
        else:
            print("schedule table not found.")
            
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")

if __name__ == "__main__":
    check_schedule()
