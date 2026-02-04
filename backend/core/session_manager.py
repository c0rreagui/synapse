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
            "last_seo_audit": profile.last_seo_audit,
            "stats": profile.last_seo_audit.get("stats", {}) if profile.last_seo_audit else {},
            "stats": profile.last_seo_audit.get("stats", {}) if profile.last_seo_audit else {},
            "latest_videos": profile.last_seo_audit.get("latest_videos", []) if profile.last_seo_audit else [],
            "last_error_screenshot": profile.last_seo_audit.get("last_error_screenshot") if profile.last_seo_audit else None
        }
    except Exception as e:
        print(f"DB Error getting metadata: {e}")
        return {}
    finally:
        db.close()



def check_cookies_validity(cookies: List[Dict[str, Any]]) -> bool:
    """
    Checks if the cookies contain valid (non-expired) session identifiers.
    """
    try:
        required_cookies = ["sessionid"] # sessionid_ss is optional/redundant often
        found_cookies = {}
        
        current_time = time.time()
        
        for p in cookies:
            name = p.get("name")
            if name in required_cookies:
                # Check expiration
                expiry = p.get("expirationDate")
                if expiry:
                     # Check if expired
                     if expiry < current_time:
                         return False # Expired
                
                found_cookies[name] = True

        # Check if all required are found
        return all(found_cookies.get(name) for name in required_cookies)
        
    except Exception:
        return False

def list_available_sessions() -> List[Dict[str, str]]:
    """
    Returns a list of available profiles from SQLite.
    Also checks file validity for session_valid status.
    """
    db = SessionLocal()
    sessions = []
    
    # Pre-fetch all profiles from DB
    db_profiles = []
    try:
        db_profiles = db.query(Profile).all()
    except Exception as e:
        print(f"DB Error listing sessions: {e}")
    finally:
        db.close()

    # Iterate DB profiles and enrich with session status from file
    for p in db_profiles:
        profile_data = {
            "id": p.slug,
            "label": p.label or p.slug,
            "username": p.username or "",
            "avatar_url": p.avatar_url or "",
            "icon": p.icon or "",
            "status": "active" if p.active else "inactive",
            "session_valid": False # Default
        }
        
        # Check actual file for validity
        try:
             session_path = get_session_path(p.slug)
             if os.path.exists(session_path):
                 with open(session_path, 'r', encoding='utf-8') as f:
                     data = json.load(f)
                     cookies = data.get("cookies", []) if isinstance(data, dict) else data
                     if isinstance(cookies, list):
                         profile_data["session_valid"] = check_cookies_validity(cookies)
        except Exception:
            pass # Keep as False
        
        # Add error screenshot if available
        if p.last_seo_audit:
            profile_data["last_error_screenshot"] = p.last_seo_audit.get("last_error_screenshot")
            
        sessions.append(profile_data)
            
    # 2. Scan Files for sessions missing in DB (Legacy/Sync fallback)
    try:
        json_files = glob.glob(os.path.join(SESSIONS_DIR, "*.json"))
        for file_path in json_files:
            try:
                slug = os.path.splitext(os.path.basename(file_path))[0]
                
                # Skip if already in DB results
                if any(s['id'] == slug for s in sessions):
                    continue

                # Read file to get metadata
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, dict):
                     # Could be raw list
                     if isinstance(data, list):
                         # Wrap it implicitly for logic below or normalize
                         data = {"cookies": data}
                     else:
                        data = {}

                meta = data.get("synapse_meta", {})
                cookies = data.get("cookies", []) if "cookies" in data else (data if isinstance(data, list) else [])

                is_valid = False
                if isinstance(cookies, list):
                    is_valid = check_cookies_validity(cookies)
                
                sessions.append({
                    "id": slug,
                    "label": meta.get("display_name") or slug,
                    "username": meta.get("username") or "",
                    "avatar_url": meta.get("avatar_url") or "",
                    "icon": "👤",
                    "status": "active",
                    "session_valid": is_valid
                })
            except Exception as e:
                print(f"Error processing session file {file_path}: {str(e)}")
                
    except Exception as e:
        print(f"Critical Error scanning session files: {str(e)}")

    sessions.sort(key=lambda x: x['id'])
    return sessions

def import_session(label: str | None, cookies_json: str, username: str | None = None, avatar_url: str | None = None) -> str:
    """
    Imports a new session from a cookies JSON string.
    Generates a unique profile ID and creates DB entry.
    """
    # Generate ID based on timestamp
    time.sleep(0.01) # Ensure uniqueness if called in rapid succession
    profile_id = f"tiktok_profile_{int(time.time() * 1000)}" # Use ms for better resolution
    
    # Handle empty strings from frontend
    if username == "": username = None
    if avatar_url == "": avatar_url = None
    if label == "": label = None

    # 1. Save Cookies File (unchanged)
    try:
        cookies_data = json.loads(cookies_json)
        
        # Sanitize cookies for Playwright compatibility
        # Playwright only accepts sameSite values: "Strict", "Lax", "None"
        if isinstance(cookies_data, list):
            for cookie in cookies_data:
                if isinstance(cookie, dict):
                    # Normalize sameSite
                    same_site = cookie.get("sameSite", "")
                    if isinstance(same_site, str):
                        same_site_lower = same_site.lower()
                        if same_site_lower in ("strict",):
                            cookie["sameSite"] = "Strict"
                        elif same_site_lower in ("lax",):
                            cookie["sameSite"] = "Lax"
                        elif same_site_lower in ("none", "no_restriction"):
                            cookie["sameSite"] = "None"
                        else:
                            # Default unspecified/unknown to Lax
                            cookie["sameSite"] = "Lax"
                    else:
                        cookie["sameSite"] = "Lax"
                        
                    # Remove unsupported properties
                    for key in list(cookie.keys()):
                        if key not in ("name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"):
                            del cookie[key]
                    
                    # Rename expirationDate to expires if present
                    if "expirationDate" in cookie:
                        cookie["expires"] = cookie.pop("expirationDate")
        
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
        # Determine final label
        final_label = label
        if not final_label or not final_label.strip():
            final_label = username if username else f"Novo Perfil {int(time.time())}"
        
        new_profile = Profile(
            slug=profile_id,
            label=final_label,
            username=username, # Use provided username or None
            avatar_url=avatar_url, # Use provided avatar or None
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
        # Safe print for Windows console
        import traceback
        traceback.print_exc()
        print(f"DB Error creating profile: {repr(e)}")
        raise ValueError(f"Database error: {e}")
    finally:
        db.close()
        
    return profile_id

def update_profile_metadata_async(profile_id: str):
    """
    Background task to fetch metadata from TikTok using requests.
    Updates the profile in DB if successful.
    """
    import requests
    from fake_useragent import UserAgent
    
    print(f"Starting metadata fetch for {profile_id}...")
    
    # helper to find cookie value
    def get_cookie_value(name, cookies):
        for c in cookies:
             if c.get("name") == name:
                 return c.get("value")
        return None

    try:
        session_path = get_session_path(profile_id)
        if not os.path.exists(session_path):
            return

        with open(session_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            raw_cookies = data.get("cookies", []) if isinstance(data, dict) else data

        # Prepare requests session
        s = requests.Session()
        # reconstruct cookies for requests
        for c in raw_cookies:
            s.cookies.set(c.get("name"), c.get("value"), domain=c.get("domain", ".tiktok.com"))
            
        # Headers
        ua = UserAgent()
        headers = {
            "User-Agent": ua.random,
            "Referer": "https://www.tiktok.com/",
            "Origin": "https://www.tiktok.com"
        }
        
        # We attempt to fetch the main page or upload page to scraping bits
        # BUT SCRAPING TIKTOK IS HARD due to hydration.
        # Check if we can find 'username' in cookies first?
        # Typically 'sid_guard' or others don't have username.
        # Let's try to hit an API endpoint if possible, or just the main page.
        
        r = s.get("https://www.tiktok.com/passport/web/account/info/", headers=headers, timeout=10)
        
        username = None
        avatar_url = None
        
        if r.status_code == 200:
             json_data = r.json()
             if "data" in json_data and "username" in json_data["data"]:
                 username = json_data["data"]["username"]
                 avatar_url = json_data["data"].get("avatar_url")
                 
        if username:
            print(f"Metadata found: {username}")
            update_profile_info(profile_id, {
                "username": username,
                "label": username, # Auto-update label to username
                "avatar_url": avatar_url
            })
        else:
            print("Could not fetch metadata via API.")
            
    except Exception as e:
        print(f"Error fetching metadata for {profile_id}: {e}")

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
        if "label" in info:
            profile.label = info["label"]
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

        if "latest_videos" in updates:
             # Store videos in last_seo_audit
             current_audit = dict(profile.last_seo_audit) if profile.last_seo_audit else {}
             current_audit["latest_videos"] = updates["latest_videos"]
             profile.last_seo_audit = current_audit

        if "last_error_screenshot" in updates:
             current_audit = dict(profile.last_seo_audit) if profile.last_seo_audit else {}
             current_audit["last_error_screenshot"] = updates["last_error_screenshot"]
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
        
        if profile:
            # 2. Delete related Audits (FK constraint)
            from core.models import Audit, ScheduleItem
            
            db.query(Audit).filter(Audit.profile_id == profile.id).delete()
            
            # 3. Delete related Schedule Items (Loose slug link)
            db.query(ScheduleItem).filter(ScheduleItem.profile_slug == profile_id).delete()

            # 4. Delete Profile
            db.delete(profile)
            db.commit()
        else:
             print(f"Warning: Profile {profile_id} not found in DB, proceeding to check file.")
        
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
        # Safe print
        import traceback
        traceback.print_exc()
        print(f"DB Error deleting session: {repr(e)}")
        return False
    finally:
        db.close()

def update_profile_status(profile_id: str, active: bool) -> bool:
    """
    Updates just the active status of a profile.
    """
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.slug == profile_id).first()
        if not profile: return False
        
        profile.active = active
        profile.updated_at = datetime.utcnow()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error updating status: {e}")
        return False
    finally:
        db.close()
