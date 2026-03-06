import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "data", "synapse.db")

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("ALTER TABLE proxies ADD COLUMN nickname VARCHAR;")
    conn.commit()
    print("Column added successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
