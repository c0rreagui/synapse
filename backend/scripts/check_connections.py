
import asyncio
import sys
import os
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core.queue_manager import QueueManager
from core.storage import s3_storage

async def check_all():
    print("[DIAGNOSTIC] Checking System Connections...")
    errors = []

    # 1. PostgreSQL
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("[OK] PostgreSQL: Connected")
    except Exception as e:
        print(f"[FAIL] PostgreSQL: Failed ({e})")
        errors.append("postgres")

    # 2. Redis
    try:
        pool = await QueueManager.get_pool()
        await pool.ping()
        print("[OK] Redis: Connected")
    except Exception as e:
        print(f"[FAIL] Redis: Failed ({e})")
        errors.append("redis")

    # 3. MinIO
    try:
        s3_storage.client.head_bucket(Bucket=s3_storage.bucket)
        print("[OK] MinIO: Connected")
    except Exception as e:
        print(f"[FAIL] MinIO: Failed ({e})")
        errors.append("minio")

    if errors:
        print(f"[ERROR] System Check Failed for: {', '.join(errors)}")
        sys.exit(1)
    else:
        print("[SUCCESS] ALL SYSTEMS GO!")
        sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(check_all())
    except KeyboardInterrupt:
        pass
