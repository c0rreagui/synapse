import sqlite3
import os

DB_PATH = r"d:\APPS - ANTIGRAVITY\Synapse\synapse.db"

def set_event_completed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Find the first pending event
    cursor.execute("SELECT id, scheduled_time FROM schedule ORDER BY scheduled_time DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        eid, time = row
        print(f"Updating event {eid} (at {time}) to 'completed'")
        cursor.execute("UPDATE schedule SET status='completed' WHERE id=?", (eid,))
        conn.commit()
    else:
        print("No events found")
    conn.close()

if __name__ == "__main__":
    set_event_completed()
