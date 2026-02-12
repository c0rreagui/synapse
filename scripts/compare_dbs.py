
import sqlite3
import os

def check_db(path):
    print(f"\n--- Checking DB: {path} ---")
    if not os.path.exists(path):
        print("File does not exist")
        return
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, slug, label, active FROM profiles")
        rows = cursor.fetchall()
        print(f"Total Profiles: {len(rows)}")
        for r in rows:
            print(f"ID: {r[0]} | Slug: {r[1]} | Label: {r[2]} | Active: {r[3]}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db("synapse.db")
    check_db("backend/synapse.db")
