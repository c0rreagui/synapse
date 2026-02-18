import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import scripts.script_env
scripts.script_env.setup_script_env()

from sqlalchemy import create_engine, text

# Connect to Postgres
DATABASE_URL = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
engine = create_engine(DATABASE_URL)

print("=== MONITORAMENTO ITEM 31 ===\n")
print("Aguardando execução às 02:09:34...\n")

# Monitor for 8 minutes (every 30 seconds)
for i in range(16):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, status, scheduled_time, error_message, posted_url
            FROM schedule 
            WHERE id = 31
        """))
        
        item = result.fetchone()
        
        if item:
            item_id, status, scheduled_time, error_msg, posted_url = item
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Item 31: status={status}")
            
            if error_msg:
                print(f"          Error: {error_msg}")
            
            if posted_url:
                print(f"          URL: {posted_url}")
            
            if status in ['completed', 'posted']:
                print(f"\n[SUCESSO] Item 31 concluído com status: {status}")
                break
            elif status == 'failed':
                print(f"\n[FALHA] Item 31 falhou!")
                if error_msg:
                    print(f"Mensagem: {error_msg}")
                break
    
    if i < 15:
        time.sleep(30)

print("\n[FIM] Monitoramento concluído")
