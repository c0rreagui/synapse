import os
import glob
from typing import List, Dict

# CONSTANTS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

def get_session_path(session_name: str) -> str:
    """Returns the absolute path for a session file."""
    return os.path.join(SESSIONS_DIR, f"{session_name}.json")

def session_exists(session_name: str) -> bool:
    """Checks if a session file exists."""
    return os.path.exists(get_session_path(session_name))

def list_available_sessions() -> List[Dict[str, str]]:
    """
    Scans the sessions directory and returns a list of available profiles.
    Returns: [{'id': 'tiktok_profile_01', 'label': 'Perfile 01 (Cortes)', 'status': 'active'}]
    """
    sessions = []
    if not os.path.exists(SESSIONS_DIR):
        return []
        
    # List all .json files in sessions dir
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json") and filename.startswith("tiktok_profile"):
            profile_id = filename.replace(".json", "")
            
            # Formata o label para ficar amigável
            # Ex: tiktok_profile_01 -> Perfil 01
            clean_name = profile_id.replace("tiktok_profile_", "").replace("_", " ").title()
            label = f"Perfil {clean_name}"
            
            # Adiciona metadados manuais conhecidos (Mock para MVP)
            if "01" in profile_id: label = f"✂️ {label} (Cortes)"
            if "02" in profile_id: label = f"🔥 {label} (Ibope)"
            
            sessions.append({
                "id": profile_id,
                "label": label,
                "status": "active" # Futuramente validaremos o cookie
            })
            
    # Sort by ID to ensure consistency
    sessions.sort(key=lambda x: x['id'])
    return sessions
