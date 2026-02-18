import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text
from datetime import datetime

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

target_time = "2026-02-15 00:35:00"

with engine.connect() as conn:
    # Get current item info
    result = conn.execute(text("SELECT id, status, video_path, scheduled_time FROM schedule_items WHERE id = 31"))
    item = result.fetchone()
    
    if item:
        print(f"Item 31 Current State:")
        print(f"  Status: {item[1]}")
        print(f"  video_path: {item[2]}")
        print(f"  scheduled_time: {item[3]}")
        
        # Update item
        conn.execute(text("""
            UPDATE schedule_items 
            SET scheduled_time = :time,
                status = 'pending',
                error_message = NULL
            WHERE id = 31
        """), {"time": target_time})
        
        conn.commit()
        
        print(f"\nItem 31 Updated:")
        print(f"  scheduled_time: {target_time}")
        print(f"  status: pending")
        print(f"  error_message: NULL")
    else:
        print("Item 31 not found!")
