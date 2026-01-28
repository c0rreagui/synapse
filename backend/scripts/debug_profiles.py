
import sys
import os
import asyncio
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.session_manager import list_available_sessions

print("--- TESTING LIST_AVAILABLE_SESSIONS ---")
try:
    sessions = list_available_sessions()
    print(json.dumps(sessions, indent=2))
except Exception as e:
    print(f"ERROR: {e}")
