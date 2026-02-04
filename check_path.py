import sqlite3
import os

db_path = 'backend/synapse.db'
try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT video_path FROM schedule WHERE id = 1")
    row = cur.fetchone()
    if row:
        print(f"Video Path in DB: {row[0]}")
        norm_path = row[0]
        # Simulate normalization
        if norm_path.startswith("/app/data/"):
            norm_path = norm_path.replace("/app/data/", "backend/data/") # Rough approx
        elif norm_path.startswith("/app/"):
             norm_path = norm_path.replace("/app/", "backend/")
        
        print(f"Checking existence of: {norm_path}")
        print(f"Exists? {os.path.exists(norm_path)}")

        # Also check absolute path if it is one
        if os.path.isabs(row[0]):
             print(f"Exists (Absolute)? {os.path.exists(row[0])}")

    con.close()
except Exception as e:
    print(e)
