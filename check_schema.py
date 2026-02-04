import sqlite3
import os

db_path = 'backend/synapse.db'
if not os.path.exists(db_path):
    print("DB not found")
    exit()

print(f"Using DB: {db_path}")

try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("PRAGMA table_info(schedule)")
    columns = cur.fetchall()
    for col in columns:
        print(col)
        
    print("-" * 20)
    # Just grab all from pending to see
    cur.execute("SELECT * FROM schedule WHERE status = 'pending' LIMIT 1")
    row = cur.fetchone()
    if row:
        print("Sample pending row:", row)
    else:
        print("No pending rows found")
        
    con.close()
except Exception as e:
    print(e)
