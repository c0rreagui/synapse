import sqlite3
import os

db_path = r'd:\APPS - ANTIGRAVITY\Synapse\backend\synapse.db'
if not os.path.exists(db_path):
    print("DB FILE NOT FOUND")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_templates'")
    rows = cursor.fetchall()
    print(f"Tables found: {rows}")
except Exception as e:
    print(f"Error: {e}")
conn.close()
