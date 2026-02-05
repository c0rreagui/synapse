import sys
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.append(os.path.join(os.getcwd(), "backend"))

# 1. Test Session Manager Timezone
from core.session_manager import update_profile_status, get_profile_metadata
from core.database import SessionLocal
from core.models import Profile

# Create dummy profile if needed
db = SessionLocal()
pid = "test_timezone_profile"
try:
    p = db.query(Profile).filter(Profile.slug == pid).first()
    if not p:
        p = Profile(slug=pid, label="Test TZ", active=True, last_seo_audit={})
        db.add(p)
        db.commit()
finally:
    db.close()

# Update
print("Updating profile status...")
update_profile_status(pid, True)

# Check DB
db = SessionLocal()
try:
    p = db.query(Profile).filter(Profile.slug == pid).first()
    updated_at = p.updated_at
    print(f"Updated At (DB): {updated_at}")
    
    # Verify deviation from SP time
    sp_now = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
    diff = abs((sp_now - updated_at).total_seconds())
    print(f"SP Now: {sp_now}")
    print(f"Difference: {diff:.2f} seconds")
    
    if diff < 5:
        print("✅ Timezone check passed (Matches SP Local Time)")
    else:
        print("❌ Timezone check failed (Difference > 5s)")

finally:
    db.close()

# 2. Test Logger
from core.logger import logger
logger.log("info", "Test Info log", "test_script")
logger.log("success", "Test Success log", "test_script")
stats = logger.get_stats()
print(f"Logger Stats: {stats}")
if stats["success"] > 0:
    print("✅ Logger Success accounting passed")
else:
    print("❌ Logger Success accounting failed")
