import os
import glob
import json
import time
from typing import List, Dict, Any, Optional

# CONSTANTS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")
# PROFILES_FILE is deprecated but we keep the path just in case we need to reference it for legacy sync
DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# DB Imports
from core.database import SessionLocal
from core.models import Profile

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

def get_profile_metadata(profile_id: str) -> Dict[str, Any]:
    """Reads metadata for a profile ID from SQLite."""
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.slug == profile_id).first()
        if not profile:
            return {}
        
        # Convert model to dict
        return {
            "label": profile.label,
            "username": profile.username,
            "icon": profile.icon,
            "type": profile.type,
            "active": profile.active,
            "avatar_url": profile.avatar_url,
            "bio": profile.bio,
            "oracle_best_times": profile.oracle_best_times,
            "last_seo_audit": profile.last_seo_audit
        }
    except Exception as e:
        print(f"DB Error getting metadata: {e}")
        return {}
    finally:
        db.close()

def list_available_sessions() -> List[Dict[str, str]]:
    """
    Returns a list of available profiles from SQLite.
    """
    db = SessionLocal()
    sessions = []
    try:
        profiles = db.query(Profile).all()
        for p in profiles:
            # Basic info for the list
            sessions.append({
                "id": p.slug,
                "label": p.label or p.slug,
                "username": p.username,
                "avatar_url": p.avatar_url,
                "icon": p.icon,
                "status": "active" if p.active else "inactive"
            })
    except Exception as e:
        print(f"DB Error listing sessions: {e}")
    finally:
        db.close()
            
    # Sort by ID or Label? ID for consistency with old behavior
    sessions.sort(key=lambda x: x['id'])
    return sessions

def import_session(label: str, cookies_json: str) -> str:
    """
    Imports a new session from a cookies JSON string.
    Generates a unique profile ID and creates DB entry.
    """
    # Generate ID based on timestamp
    profile_id = f"tiktok_profile_{int(time.time())}"
    
    # 1. Save Cookies File (unchanged)
    try:
        cookies_data = json.loads(cookies_json)
        
        session_path = get_session_path(profile_id)
        # Heuristic for wrapping
        content_to_dump = cookies_data
        if isinstance(cookies_data, list):
             content_to_dump = {
                "cookies": cookies_data,
                "origins": []
            }
            
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(content_to_dump, f, indent=2)
            
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")

    # 2. Create DB Entry
    db = SessionLocal()
    try:
        new_profile = Profile(
            slug=profile_id,
            label=label,
            username=None, # Will be fetched later by validator
            icon="👤",
            type="imported",
            active=True,
            oracle_best_times=[],
            last_seo_audit={}
        )
        db.add(new_profile)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"DB Error creating profile: {e}")
        raise ValueError(f"Database error: {e}")
    finally:
        db.close()
        
    return profile_id

def update_profile_info(profile_id: str, info: Dict[str, Any]) -> bool:
    """
    Updates existing profile metadata (avatar, label, etc) in SQLite.
    """
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.slug == profile_id).first()
        if not profile:
            return False
            
        if "avatar_url" in info:
            profile.avatar_url = info["avatar_url"]
        if "nickname" in info:
            profile.label = info["nickname"]
        if "username" in info:
            profile.username = info["username"]
        
        profile.updated_at = time.strftime('%Y-%m-%d %H:%M:%S') # Or use datetime object if field is DateTime (it is)
        # SQLAlchemy handles DateTime conversion if we configured it, but let's trust auto update onupdate?
        # Manually touching it allows ensuring it changes. But 'onupdate' in model handles it.
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"DB Error updating profile info: {e}")
        return False
    finally:
        db.close()

def update_profile_metadata(profile_id: str, updates: Dict[str, Any]) -> bool:
    """
    Generic update for profile metadata in SQLite.
    """
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.slug == profile_id).first()
        if not profile:
            # If not found, maybe create? Legacy created raw JSON entry.
            # But here we enforce profile existence.
            return False

        # We need to update specific columns OR the JSON columns.
        # This function is generic. Let's see what keys are usually passed.
        # usually: oracle_best_times, last_seo_audit, etc.
        
        # We need to merge JSON fields carefully.
        # SQLAlchemy with SQLite supports JSON, but full patch update might need read-modify-write.
        
        if "oracle_best_times" in updates:
            profile.oracle_best_times = updates["oracle_best_times"]
            
        if "last_seo_audit" in updates:
            profile.last_seo_audit = updates["last_seo_audit"]
            
        # If there are other arbitrary keys, we might lose them if we don't have columns.
        # But 'last_seo_audit' and 'oracle_best_times' are the main ones.
        # If we have other keys, we should probably add them to a 'metadata' flexible column if we had one.
        # For now, let's assume specific columns or modify 'last_seo_audit' if appropriate?
        # Actually legacy code just dumped everything into the JSON object. 
        # For V1 migration safety, if a key doesn't match a column, we might ignore it or put it in bio?
        # Let's check commonly used keys.
        
        if "avatar_url" in updates:
             profile.avatar_url = updates["avatar_url"]
             
        # Commit
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"DB Error updating metadata: {e}")
        return False
    finally:
        db.close()


