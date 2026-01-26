
import sqlite3
import os

DB_PATH = "synapse.db" # Check local first
if not os.path.exists(DB_PATH):
    DB_PATH = "../synapse.db.corrupted" # Falback to the backup source

print(f"Inspecting: {DB_PATH}")
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    if ('profiles',) in tables:
        cursor.execute("SELECT * FROM profiles")
        rows = cursor.fetchall()
        print(f"Profiles count: {len(rows)}")
        
    if ('schedule',) in tables:
        cursor.execute("SELECT * FROM schedule")
        rows = cursor.fetchall()
        print(f"Schedule items count: {len(rows)}")
        for r in rows:
            print(r)
    else:
        print("No 'profiles' table found.")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
