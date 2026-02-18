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

# Schedule Item 31 for 2 minutes from now
target_time = datetime.now() + timedelta(minutes=2)
target_time_str = target_time.strftime("%Y-%m-%d %H:%M:%S")

with engine.connect() as conn:
    # Reactivate Profile 2
    conn.execute(text("UPDATE profiles SET active = true WHERE slug = 'tiktok_profile_1770307556827'"))
    
    # Update item
    conn.execute(text("""
        UPDATE schedule 
        SET scheduled_time = :time,
            status = 'pending',
            error_message = NULL
        WHERE id = 31
    """), {"time": target_time_str})
    
    conn.commit()
    
    print(f"Profile 2 REATIVADO")
    print(f"Item 31 reagendado para: {target_time_str}")
    print(f"Horario atual: {datetime.now()}")
    print(f"\n[OK] TESTE FINAL - Aguardar execucao em ~2 minutos")
