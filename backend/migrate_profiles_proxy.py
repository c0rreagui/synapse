import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("ALTER TABLE profiles ADD COLUMN proxy_id INTEGER;")
    cur.execute("ALTER TABLE profiles ADD CONSTRAINT fk_proxy FOREIGN KEY (proxy_id) REFERENCES proxies(id);")
    conn.commit()
    print("Migration successful: Added proxy_id to profiles")
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals():
        conn.close()
