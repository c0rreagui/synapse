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
                "username": p.username or "",
                "avatar_url": p.avatar_url or "",
                "icon": p.icon or "",
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
from datetime import datetime

def update_profile_info(profile_id: str, info: Dict[str, Any]) -> bool:
    """
    Updates basic profile info (label, username, avatar) in SQLite.
    info dict keys: 'nickname' (maps to label), 'username', 'avatar_url', 'bio'
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
        if "bio" in info:
            profile.bio = info["bio"]
            
        # Add support for Active Status Toggle
        if "active" in info:
            profile.active = info["active"]
        
        # FIX: Use datetime object, not string
        profile.updated_at = datetime.utcnow()
        
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
            return False

        if "oracle_best_times" in updates:
            profile.oracle_best_times = updates["oracle_best_times"]
            
        if "last_seo_audit" in updates:
            # Merge logic could be better but overwriting or setting keys is fine for now
            current_audit = dict(profile.last_seo_audit) if profile.last_seo_audit else {}
            if isinstance(updates["last_seo_audit"], dict):
                current_audit.update(updates["last_seo_audit"])
            else:
                current_audit = updates["last_seo_audit"]
            profile.last_seo_audit = current_audit
            
        if "avatar_url" in updates:
             profile.avatar_url = updates["avatar_url"]

        if "bio" in updates:
            profile.bio = updates["bio"]
            
        if "stats" in updates:
            # Store stats in last_seo_audit just to have them somewhere since no columns exist
            current_audit = dict(profile.last_seo_audit) if profile.last_seo_audit else {}
            current_audit["stats"] = updates["stats"]
            profile.last_seo_audit = current_audit

        profile.updated_at = datetime.utcnow()

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"DB Error updating metadata: {e}")
        return False
    finally:
        db.close()

def delete_session(profile_id: str) -> bool:
    """
    Deletes a profile from SQLite (and its related data) and removes its session file.
    """
    db = SessionLocal()
    try:
        # 1. Find Profile
        profile = db.query(Profile).filter(Profile.slug == profile_id).first()
        if not profile:
            return False

        # 2. Delete related Audits (FK constraint)
        # Imports inside function to avoid circular imports if any, though model import is top level
        from core.models import Audit, ScheduleItem
        
        db.query(Audit).filter(Audit.profile_id == profile.id).delete()
        
        # 3. Delete related Schedule Items (Loose slug link)
        db.query(ScheduleItem).filter(ScheduleItem.profile_slug == profile_id).delete()

        # 4. Delete Profile
        db.delete(profile)
        db.commit()
        
        # 5. Delete File
        session_path = get_session_path(profile_id)
        if os.path.exists(session_path):
            try:
                os.remove(session_path)
            except OSError as e:
                print(f"Error removing session file: {e}")
                
        return True
    except Exception as e:
        db.rollback()
        print(f"DB Error deleting profile: {e}")
        return False
    finally:
        db.close()
