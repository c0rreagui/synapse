import sqlite3
import os
import json

# Try multiple paths
paths = ['backend/synapse.db', 'synapse.db', 'backend/data/synapse.db']
db_path = None
for p in paths:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    print("DB not found in likely locations")
    exit()

print(f"Using DB: {db_path}")

try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    # Check for recent status changes too (completed/processing)
    cur.execute("SELECT id, profile_id, scheduled_time, status, metadata FROM schedule WHERE status IN ('pending', 'processing', 'completed') ORDER BY scheduled_time DESC LIMIT 5")
    rows = cur.fetchall()
    print(f"Found {len(rows)} recent items.")
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Time: {row[2]}")
        print(f"Status: {row[3]}")
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
