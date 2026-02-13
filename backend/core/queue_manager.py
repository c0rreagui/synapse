
import os
import logging
from arq import create_pool
from arq.connections import RedisSettings

logger = logging.getLogger("QueueManager")

class QueueManager:
    _pool = None

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            cls._pool = await create_pool(
                RedisSettings(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", 6379))
                )
            )
        return cls._pool

    @classmethod
    async def enqueue_upload(cls, item_id: int, video_path: str, metadata: dict):
        try:
            pool = await cls.get_pool()
            job = await pool.enqueue_job(
                'upload_video_task', 
                item_id, 
                video_path, 
                metadata
            )
            logger.info(f"✅ Job Enqueued: {job.job_id} (Item {item_id})")
            return job.job_id
        except Exception as e:
            logger.error(f"❌ Failed to enqueue job: {e}")
            raise e
