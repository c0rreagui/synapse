import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="synapse_db",
        user="synapse",
        password="synapse_password"
    )
    cur = conn.cursor()
    cur.execute("ALTER TABLE profiles ADD COLUMN proxy_id INTEGER;")
    cur.execute("ALTER TABLE profiles ADD CONSTRAINT fk_proxy FOREIGN KEY (proxy_id) REFERENCES proxies(id);")
    conn.commit()
    print("Column proxy_id added successfully to Postgres profiles table.")
except Exception as e:
    print(f"Migration error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
