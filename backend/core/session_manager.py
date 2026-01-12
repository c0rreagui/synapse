import os
import glob
from typing import List, Dict

# CONSTANTS
# session_manager.py is in: backend/core/session_manager.py
# We need BASE_DIR to be: backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

def get_session_path(session_name: str) -> str:
    """Returns the absolute path for a session file."""
    return os.path.join(SESSIONS_DIR, f"{session_name}.json")

def session_exists(session_name: str) -> bool:
    """Checks if a session file exists."""
    return os.path.exists(get_session_path(session_name))

async def save_session(context, session_name: str):
    """
    Saves the browser context storage state to the session file.
    Args:
        context: Playwright BrowserContext
        session_name: Name of the session (profile_id)
    """
    path = get_session_path(session_name)
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    await context.storage_state(path=path)

# New imports needed: json
import json
from typing import List, Dict, Any, Optional

# ... (Previous constants)
DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")

# ... (Previous functions unchanged until list_available_sessions)

def get_profile_metadata(profile_id: str) -> Dict[str, Any]:
    """Reads metadata for a profile ID."""
    if not os.path.exists(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(profile_id, {})
    except:
        return {}

def list_available_sessions() -> List[Dict[str, str]]:
    """
    Scans the sessions directory and returns a list of available profiles.
    Merges with metadata from profiles.json.
    """
    sessions = []
    if not os.path.exists(SESSIONS_DIR):
        # Even if no session files, we might want to return configured profiles?
        # Typically we only list VALID sessions (cookies). 
        # But for UI 'Profiles' list, maybe we want all configured ones?
        # Current logic scans files. Let's keep scanning files but enrich with JSON.
        pass

    # Load metadata once
    all_metadata = {}
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                all_metadata = json.load(f)
        except:
            pass
        
    # If no session files exist, maybe fallback to profiles.json keys if we treat them as "potential" sessions?
    # For now, let's list FILES as primary source of "Session Available", and PROFILES.JSON as "Config".
    # User asked for "Real Data". Real data = Cookie exists.
    
    if os.path.exists(SESSIONS_DIR):
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json") and filename.startswith("tiktok_profile"):
                profile_id = filename.replace(".json", "")
                
                # Get metadata
                meta = all_metadata.get(profile_id, {})
                
                # Default label if missing
                label = meta.get("label")
                if not label:
                    label = profile_id.replace("tiktok_profile_", "").replace("_", " ").title()
                    label = f"Perfil {label}"
                
                # Icon injection into label if needed by UI (UI expects 'label' string)
                # But better to send 'icon' field if UI supports it.
                # Current UI parses icon from label? No, UI `getProfileIcon` is hardcoded.
                # We will change UI to read `icon` field.
                
                sessions.append({
                    "id": profile_id,
                    "label": label,
                    "username": meta.get("username"), # Add username
                    "avatar_url": meta.get("avatar_url"), # Add avatar_url
                    "icon": meta.get("icon", "👤"),
                    "status": "active"
                })
    
    # Also Check for profiles in JSON that might NOT have a session file yet (optional)
    # create_session script creates the file.
            
    # Sort by ID
    sessions.sort(key=lambda x: x['id'])
    return sessions

def import_session(label: str, cookies_json: str) -> str:
    """
    Imports a new session from a cookies JSON string.
    Generates a unique profile ID.
    """
    import time
    
    # Generate ID based on timestamp
    profile_id = f"tiktok_profile_{int(time.time())}"
    
    # Save Cookies File
    try:
        # Validate JSON
        cookies_data = json.loads(cookies_json)
        
        # Save to sessions dir
        session_path = get_session_path(profile_id)
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump({
                "cookies": cookies_data,
                "origins": [
                    {
                        "origin": "https://www.tiktok.com",
                        "localStorage": []
                    }
                ] 
            }, f, indent=2) # Wrap in Playwright storage format structure if raw cookies
            # NOTE: If user pastes raw array of cookies, we might need to wrap it.
            # Assuming user pastes the full storage state OR just cookies. 
            # Ideally the tool exports full state. Use heuristic?
            # For simplicity, if list, wrap. If dict, dump as is.
            
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")
        
    # Heuristic for wrapping if just cookies array
    if isinstance(cookies_data, list):
         with open(session_path, 'w', encoding='utf-8') as f:
            json.dump({
                "cookies": cookies_data,
                "origins": []
            }, f, indent=2)
    else:
         with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(cookies_data, f, indent=2)

    # Update profiles.json metadata
    all_metadata = {}
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                all_metadata = json.load(f)
        except:
            pass
            
    all_metadata[profile_id] = {
        "label": label,
        "icon": "👤",
        "type": "imported",
        "active": True
    }
    
    with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=4)
        
    return profile_id

def update_profile_info(profile_id: str, info: Dict[str, Any]) -> bool:
    """
    Updates existing profile metadata (avatar, label, etc).
    """
    if not os.path.exists(PROFILES_FILE):
        return False
        
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if profile_id in data:
            # Update fields
            current = data[profile_id]
            if "avatar_url" in info:
                current["avatar_url"] = info["avatar_url"]
                # Also set icon to custom char if wanted, or just keep avatar_url for frontend to use
            if "nickname" in info:
                current["label"] = info["nickname"]
            if "username" in info:
                current["username"] = info["username"]
            
            data[profile_id] = current
            
            with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        return False
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False

def update_profile_metadata(profile_id: str, updates: Dict[str, Any]) -> bool:
    """
    Generic update for profile metadata in profiles.json.
    Used to store Oracle insights, best times, etc.
    """
    if not os.path.exists(PROFILES_FILE):
        return False
        
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if profile_id not in data:
            data[profile_id] = {} # Create if valid session exists but no metadata? Or strict?

        # Merge updates
        data[profile_id].update(updates)
        
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error updating profile metadata: {e}")
        return False


