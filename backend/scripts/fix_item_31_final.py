import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

target_time = "2026-02-15 01:20:00"  # Next multiple of 5

with engine.connect() as conn:
    # Get current item info - CORRECT TABLE NAME: schedule (not scheduled_items)
    result = conn.execute(text("SELECT id, profile_slug, status, video_path, scheduled_time FROM schedule WHERE id = 31"))
    item = result.fetchone()
    
    if item:
        print(f"Item 31 Current State:")
        print(f"  profile_slug: {item[1]}")
        print(f"  Status: {item[2]}")
        print(f"  video_path: {item[3]}")
        print(f"  scheduled_time: {item[4]}")
        
        # Update item - change profile_slug to tiktok_profile_1770307556827 (Opinião Viral - Active)
        conn.execute(text("""
            UPDATE schedule 
            SET scheduled_time = :time,
                status = 'pending',
                error_message = NULL,
                profile_slug = 'tiktok_profile_1770307556827'
            WHERE id = 31
        """), {"time": target_time})
        
        conn.commit()
        
        print(f"\nItem 31 Updated:")
        print(f"  profile_slug: tiktok_profile_1770307556827 (Opinião Viral)")
        print(f"  scheduled_time: {target_time}")
        print(f"  status: pending")
        print(f"  error_message: NULL")
    else:
        print("Item 31 not found!")
