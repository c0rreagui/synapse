import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database import SessionLocal
from core.models import ScheduleItem

def reschedule_now():
    db = SessionLocal()
    try:
        items = db.query(ScheduleItem).filter(ScheduleItem.id.in_([41, 42])).all()
        next_time = datetime.now() + timedelta(minutes=2)
        
        for item in items:
            print(f"[REFRESH] Reagendando Item {item.id} de {item.status} para PENDING em {next_time}")
            item.status = "pending"
            item.scheduled_time = next_time
            item.error_message = None # Limpa erro anterior
            
        db.commit()
        print("[SUCCESS] Itens reagendados com sucesso.")
    except Exception as e:
        print(f"[ERROR] Erro ao reagendar: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reschedule_now()
