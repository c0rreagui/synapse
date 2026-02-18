
import sqlite3

DB_PATH = r"d:\APPS - ANTIGRAVITY\Synapse\backend\synapse.db"

def list_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    # helper to print schema of a likely queue table
    for t in tables:
        name = t[0]
        if True: # Force inspect all
            print(f"\nSchema for {name}:")
            cursor.execute(f"PRAGMA table_info({name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")

    conn.close()

if __name__ == "__main__":
    list_tables()
