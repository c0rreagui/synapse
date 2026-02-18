from datetime import datetime
from zoneinfo import ZoneInfo
import os

sp_tz = ZoneInfo("America/Sao_Paulo")
now = datetime.now(sp_tz)
print(f"Scheduler NOW (SP): {now}")
print(f"System NOW: {datetime.now()}")
