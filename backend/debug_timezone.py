
import sys
import os
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import SessionLocal, Base, engine
from core.models import ScheduleItem

def test_timezone_update():
    print("=== TESTING TIMEZONE UPDATE ===")
    
    # 1. Simulator Frontend Input: 15:40 SP -> 18:40 UTC
    # Frontend sends ISO string
    input_iso = "2026-02-10T18:40:00.000Z" 
    print(f"Frontend Input: {input_iso}")
    
    # 2. Simulate Backend Logic
    clean_time = input_iso.replace("Z", "+00:00")
    dt_obj = datetime.fromisoformat(clean_time)
    print(f"Parsed Object: {dt_obj} (tz={dt_obj.tzinfo})")
    
    # 3. Simulate DB Save/Load (Naive simulation)
    # If DB stores as generic DateTime, it usually strips TZ if not supported
    # Let's say it stores the naive part: 18:40
    dt_naive_db = dt_obj.replace(tzinfo=None) 
    print(f"DB Stored (Simulated Naive): {dt_naive_db}")
    
    # 4. Simulate Read & Return Logic
    # Original logic: item.scheduled_time.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
    sp_tz = ZoneInfo("America/Sao_Paulo")
    
    # Scenario A: DB returns Naive
    result_naive = dt_naive_db.replace(tzinfo=sp_tz)
    print(f"Result (if DB returns Naive): {result_naive.isoformat()}")
    
    # Scenario B: DB returns Aware (UTC)
    dt_aware_db = dt_obj # It was +00:00
    if dt_aware_db.tzinfo is None:
         result_aware = dt_aware_db.replace(tzinfo=sp_tz)
    else:
         result_aware = dt_aware_db.isoformat()
    print(f"Result (if DB returns Aware): {result_aware}")

    # 5. Correct Logic Attempt
    # We want 15:40 SP.
    # Input 18:40 UTC.
    # If we convert input to SP first:
    dt_sp = dt_obj.astimezone(sp_tz)
    print(f"Correct conversion to SP: {dt_sp}")
    
    # What the user sees
    print("\nCONCLUSION:")
    print(f"User expects: 15:40 SP")
    print(f"Current Logic (Scenario A) gives: {result_naive.strftime('%H:%M')} SP (This is 18:40 SP!)")
    print(f"  -> User sees 18:40 instead of 15:40. Shifted +3h.")

if __name__ == "__main__":
    test_timezone_update()
