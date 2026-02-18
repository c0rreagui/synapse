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

print(f"Iniciando monitoramento do Item 31 às {datetime.now()}")
print("Horário alvo: 01:40:00")
print("Aguardando execução...\n")

for i in range(12):  # Monitor for 12 minutes (1 min intervals)
    time.sleep(60)  # Wait 1 minute
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, status, scheduled_time, error_message FROM schedule WHERE id = 31"))
        item = result.fetchone()
        
        if item:
            current_time = datetime.now()
            print(f"[{current_time.strftime('%H:%M:%S')}] Item 31 - Status: {item[1]}, Scheduled: {item[2]}, Error: {item[3]}")
            
            if item[1] in ['completed', 'posted', 'success']:
                print(f"\n✅ SUCESSO! Item 31 foi postado com status: {item[1]}")
                break
            elif item[1] == 'failed' and i > 2:  # Only report failure after 01:42
                print(f"\n❌ FALHA! Item 31 falhou com erro: {item[3]}")
                break
        else:
            print(f"[{current_time.strftime('%H:%M:%S')}] Item 31 não encontrado!")
            break

print("\nMonitoramento concluído.")
