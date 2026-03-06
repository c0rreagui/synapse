from core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE proxies ADD COLUMN nickname VARCHAR;"))
        conn.commit()
    print("Column added successfully to Postgres.")
except Exception as e:
    print(f"Migration error: {e}")
