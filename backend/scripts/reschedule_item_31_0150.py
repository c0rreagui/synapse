import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

target_time = "2026-02-15 01:50:00"  # 20 min from now (01:30)

with engine.connect() as conn:
    # Update item - target time 20min ahead
    conn.execute(text("""
        UPDATE schedule 
        SET scheduled_time = :time,
            status = 'pending',
            error_message = NULL
        WHERE id = 31
    """), {"time": target_time})
    
    conn.commit()
    
    print(f"Item 31 reagendado para: {target_time}")
