
import sqlite3
import os
import sys

DB_PATH = r"d:\APPS - ANTIGRAVITY\Synapse\backend\synapse.db"

def fix_stuck_item():
    if not os.path.exists(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find the item
    cursor.execute("SELECT id, status, video_path FROM schedule WHERE video_path LIKE '%ptest_cb_profile%'")
    items = cursor.fetchall()

    if not items:
        print("No item found with filename containing 'ptest_cb_profile'")
        cursor.execute("SELECT id, status, video_path FROM schedule WHERE status='processing'")
        print("Other processing items:", cursor.fetchall())
    else:
        print(f"Found {len(items)} items:")
        for item in items:
            print(f"  ID: {item[0]}, Status: {item[1]}, File: {item[2]}")
            
            # Update to FAILED
            cursor.execute("UPDATE schedule SET status='failed', error_message='Manually failed to stop CB loop' WHERE id=?", (item[0],))
            print(f"  -> Marked ID {item[0]} as FAILED")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_stuck_item()
