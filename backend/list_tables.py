
import sqlite3

def list_tables():
    conn = sqlite3.connect("sql_app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:", tables)
    conn.close()

if __name__ == "__main__":
    list_tables()
