
import sqlite3
import sys

def update_time():
    db_path = r'd:\APPS - ANTIGRAVITY\Synapse\backend\synapse.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Force time to 14:10
    target_time = "2026-02-04 14:10:00"
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables:", c.fetchall())
    # Force time to 14:10
    target_time = "2026-02-04 14:10:00"
    try:
        c.execute("UPDATE schedule SET scheduled_time = ? WHERE id = 1", (target_time,))
        conn.commit()
        print(f"Updated Item 1 to {target_time} in table 'schedule'")
    except Exception as e:
        print(f"Error on update: {e}")
        c.execute("PRAGMA table_info(schedule)")
        print("Columns:", c.fetchall())
    conn.close()

if __name__ == "__main__":
    update_time()
