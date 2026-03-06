from core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE profiles ADD COLUMN proxy_id INTEGER;"))
        conn.execute(text("ALTER TABLE profiles ADD CONSTRAINT fk_proxy FOREIGN KEY (proxy_id) REFERENCES proxies(id);"))
        conn.commit()
    print("Column added successfully to Postgres profiles.")
except Exception as e:
    print(f"Migration error: {e}")
