import sqlite3
import os
import json

db_path = 'backend/synapse.db'
try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT id, profile_slug, scheduled_time, status, metadata_info FROM schedule ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    print(f"Found {len(rows)} items.")
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Profile: {row[1]}")
        print(f"Time: {row[2]}")
        print(f"Status: {row[3]}")
        try:
            meta = json.loads(row[4]) if row[4] else {}
            print(f"Privacy: {meta.get('privacy_level', 'Not Set')}")
        except:
            print(f"Metadata: {row[4]}")
        print("-" * 20)
    con.close()
except Exception as e:
    print(e)
