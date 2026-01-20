from core import session_manager
import json
import os

profile_id = "vibe.corteseclips"
# Force ensure profile exists in JSON
if not session_manager.update_profile_metadata(profile_id, {}):
    # If it returned False, it might be due to file missing or other error.
    # Let's try manually ensuring it.
    print("⚠️ Update returned False, checking file...")

data = {
    "oracle_best_times": [
        {"day": "Monday", "hour": 10, "reason": "High engagement"},
        {"day": "Wednesday", "hour": 14, "reason": "Prime time"},
        {"day": "Friday", "hour": 18, "reason": "Weekend logic"}
    ],
    "oracle_last_run": "2026-01-19T00:00:00",
    "label": "Vibe Teste",
    "username": "vibe.corteseclips"
}

success = session_manager.update_profile_metadata(profile_id, data)
if success:
    print(f"✅ Injected test data for {profile_id}")
else:
    print(f"❌ Failed to inject data for {profile_id}")
