
import sqlite3
import os

db_path = r"d:\APPS - ANTIGRAVITY\Synapse\backend\data\synapse.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    # Try alternate location
    db_path = r"d:\APPS - ANTIGRAVITY\Synapse\backend\synapse.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, label, avatar_url, active, slug FROM profiles")
        rows = cursor.fetchall()
        print("Profiles found:")
        for row in rows:
            print(f"ID: {row[0]}, Username: {row[1]}, Label: {row[2]}, Avatar: {row[3][:30]}..., Active: {row[4]}, Slug: {row[5]}")
    except Exception as e:
        print(f"Error querying database: {e}")
    conn.close()
else:
    print("Database file still not found.")
