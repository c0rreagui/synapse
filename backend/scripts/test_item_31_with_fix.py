import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

# Schedule Item 31 for 5 minutes from now
target_time = datetime.now() + timedelta(minutes=5)
target_time_str = target_time.strftime("%Y-%m-%d %H:%M:%S")

with engine.connect() as conn:
    # Update item
    conn.execute(text("""
        UPDATE schedule 
        SET scheduled_time = :time,
            status = 'pending',
            error_message = NULL
        WHERE id = 31
    """), {"time": target_time_str})
    
    conn.commit()
    
    print(f"Item 31 reagendado para: {target_time_str}")
    print(f"Horário atual: {datetime.now()}")
    print(f"\n[OK] Aguardar execução em ~5 minutos")
