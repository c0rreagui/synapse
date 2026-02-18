import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__),'..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text
from datetime import datetime

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

# Using existing video for profile 2
correct_video_path = "/app/data/pending/ptiktok_profile_1770307556827_1463ab54.mp4"
target_time = "2026-02-15 02:00:00"

with engine.connect() as conn:
    # Update item with correct video path
    conn.execute(text("""
        UPDATE schedule 
        SET video_path = :video_path,
            scheduled_time = :time,
            status = 'pending',
            error_message = NULL
        WHERE id = 31
    """), {"video_path": correct_video_path, "time": target_time})
    
    conn.commit()
    
    print(f"Item 31 atualizado:")
    print(f"  Video Path: {correct_video_path}")
    print(f"  Scheduled Time: {target_time}")
    print(f"  Horário atual: {datetime.now()}")
