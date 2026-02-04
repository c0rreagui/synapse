import sqlite3
import os
import json

db_path = 'backend/data/synapse.db'
if not os.path.exists(db_path):
    print("DB not found")
    exit()

try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT id, profile_id, scheduled_time, status, metadata FROM schedule WHERE status = 'pending' ORDER BY scheduled_time ASC")
    rows = cur.fetchall()
    print(f"Found {len(rows)} pending items.")
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Time: {row[2]}")
        print(f"Profile: {row[1]}")
        try:
            meta = json.loads(row[4])
            print(f"Privacy: {meta.get('privacy_level', 'Not Set')}")
        except:
            print(f"Metadata: {row[4]}")
        print("-" * 20)
    con.close()
except Exception as e:
    print(e)
