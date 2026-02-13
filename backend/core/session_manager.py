import os
import glob
import json
import time
from typing import List, Dict, Any, Optional

# Centralized Paths
from core.config import SESSIONS_DIR, DATA_DIR
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json") # Deprecated but kept for legacy sync

#from core.config import DATA_DIR, BASE_DIR
# DB Imports
from core.database import SessionLocal
from core.models import Profile
from core.database_utils import with_db_retries

def get_session_path(session_name: str) -> str:
    """Returns the absolute path for a session file."""
    return os.path.join(SESSIONS_DIR, f"{session_name}.json")

def get_context_path(profile_id: str) -> str:
    """Returns the absolute path for the persistent browser context."""
    return os.path.join(DATA_DIR, "contexts", profile_id)

def session_exists(session_name: str) -> bool:
    """Checks if a session file exists."""
    return os.path.exists(get_session_path(session_name))

def update_profile_status(profile_id: str, active: bool) -> bool:
    """
    Updates the 'active' status of a profile in the database.
    Called by profile_validator.py after successful/failed validation.
    Returns True if successful, False otherwise.
    """
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.slug == profile_id).first()
        if not profile:
            print(f"[update_profile_status] Profile {profile_id} not found in DB")
            return False
        
        profile.active = active
        db.commit()
        print(f"[update_profile_status] Profile {profile_id} active -> {active}")
        return True
    except Exception as e:
        print(f"[update_profile_status] Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

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


async def validate_session_for_upload(profile_id: str) -> bool:
    """
    Performs a pre-flight check to verify if the session can access TikTok Studio.
    Used by the scheduler to avoid starting heavy upload processes with dead sessions.
    [SYN-FIX] FORCE Desktop User-Agent because upload is a desktop feature.
    """
    from core.browser import launch_browser, close_browser
    from core.network_utils import get_upload_url, DEFAULT_UA
    
    session_path = get_session_path(profile_id)
    if not os.path.exists(session_path):
        return False
        
    # [SYN-FIX] Use DEFAULT_UA (Desktop) instead of profile UA to avoid Mobile -> App Store redirect
    user_agent = DEFAULT_UA
        
    p = None
    browser = None
    try:
        # Headless check is sufficient
        p, browser, context, page = await launch_browser(
            headless=True, 
            storage_state=session_path,
            user_agent=user_agent
        )
        await page.goto(get_upload_url(), timeout=30000, wait_until="domcontentloaded")
        
        current_url = page.url
        # If redirected to login, the session is definitely not enough for upload
        if "login" in current_url or "tiktok.com" not in current_url:
            return False
        
        # [SYN-FIX] Check for App Store redirect
        if "onelink.me" in current_url:
            return False
            
        return True
    except Exception:
        return False
    finally:
        if p:
            await close_browser(p, browser)

async def check_session_health_lightweight(profile_id: str) -> bool:
    """
    Lightweight check for session validity using httpx (no browser).
    Verifies if a GET to the upload page redirect to login.
    [SYN-FIX] FORCE Desktop User-Agent to avoid redirection to App Store (onelink.me) 
    if the profile was created with a Mobile User-Agent.
    """
    import httpx
    from core.network_utils import get_upload_url, get_scrape_headers, DEFAULT_UA
    
    session_path = get_session_path(profile_id)
    if not os.path.exists(session_path):
        return False
        
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cookies_list = data.get("cookies", []) if isinstance(data, dict) else data
            
        cookies_dict = {c['name']: c['value'] for c in cookies_list if isinstance(c, dict)}
        
        # [SYN-FIX] Force Desktop UA for this specific check because tiktokstudio/upload 
        # is a desktop-only route. Mobile UAs get redirected to App Store.
        desktop_ua = DEFAULT_UA 
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            headers = get_scrape_headers(user_agent=desktop_ua)
            response = await client.get(get_upload_url(), cookies=cookies_dict, headers=headers)
            
            # If the final URL contains login, it means we don't have access
            final_url = str(response.url)
            if "login" in final_url.lower() or "passport" in final_url.lower():
                return False
                
            # If we see 'upload' in the URL and status is 200, we are likely in
            # [SYN-FIX] Also check we didn't get redirected to onelink.me (App Store)
            if "onelink.me" in final_url.lower():
                 return False

            if response.status_code == 200 and "upload" in final_url.lower():
                return True
                
            return False
    except Exception:
        return False





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
                expiry = p.get("expirationDate") or p.get("expires")
                if expiry and expiry > 0:
                     # Check if expired
                     if expiry < current_time:
                         return False # Expired
                
                found_cookies[name] = True

        # Check if all required are found
        return all(found_cookies.get(name) for name in required_cookies)
        
    except Exception:
        return False

def get_profile_user_agent(profile_id: str) -> str:
    """
    Retrieves the dedicated User-Agent for a profile from its session file.
    [SYN-FIX] SELF-HEALING: If no UA is found, it generates a new random one,
    SAVES it to the file, and returns it. This ensures consistency for legacy profiles.
    """
    from core.network_utils import DEFAULT_UA, get_random_user_agent
    
    session_path = get_session_path(profile_id)
    if not os.path.exists(session_path):
        return DEFAULT_UA

    try:
        # 1. Try to read existing
        with open(session_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle legacy Array format by wrapping it now
        if isinstance(data, list):
            new_ua = get_random_user_agent()
            data = {
                "cookies": data,
                "origins": [],
                "synapse_meta": {"user_agent": new_ua}
            }
            # Save upgraded format
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return new_ua
            
        if isinstance(data, dict):
            meta = data.get("synapse_meta", {})
            ua = meta.get("user_agent")
            
            if ua:
                return ua
            else:
                # [SYN-FIX] Generate, Save, Return
                new_ua = get_random_user_agent()
                if "synapse_meta" not in data:
                    data["synapse_meta"] = {}
                data["synapse_meta"]["user_agent"] = new_ua
                
                with open(session_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                return new_ua
                
    except Exception as e:
        print(f"Error resolving User-Agent for {profile_id}: {e}")
        pass
        
    return DEFAULT_UA

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
        # Use global Profile class
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

    # Merge with DB data (if available) & Real-time Stats
    # [SYN-FIX] Bulletproof Stats: Always fetch real count from DB
    # SessionLocal and Profile are available globally (imported at top of file)
    # Only ScheduleItem needs a local import here
    from core.models import ScheduleItem
    
    db = SessionLocal()
    try:
        available_slugs = [s['id'] for s in sessions]
        
        # 1. Fetch DB Profiles for metadata override (Active status, etc)
        db_profiles = db.query(Profile).filter(Profile.slug.in_(available_slugs)).all()
        db_map = {p.slug: p for p in db_profiles}
        
        # 2. Fetch Upload Counts efficiently
        # Group by profile_slug
        from sqlalchemy import func
        upload_counts = db.query(
            ScheduleItem.profile_slug, 
            func.count(ScheduleItem.id)
        ).filter(
            ScheduleItem.status.in_(['posted', 'completed', 'published', 'success'])
        ).group_by(ScheduleItem.profile_slug).all()
        
        count_map = {slug: count for slug, count in upload_counts}
        
        for session in sessions:
            slug = session['id']
            
            # Apply DB Overrides
            db_obj = db_map.get(slug)
            if db_obj:
               session['active'] = db_obj.active
               # Prefer DB avatar if JSON is empty
               if not session.get('avatar_url') and db_obj.avatar_url:
                   session['avatar_url'] = db_obj.avatar_url
            else:
                # Profile exists in JSON but not in DB? 
                # This should be rare after sync, but we should handle it gracefully.
                # Auto-heal: In a real scenario we might want to create it, but for listing just skip DB merge.
                pass
            
            # Apply Real Stats
            real_count = count_map.get(slug, 0)
            session['uploads_count'] = real_count
            
            # Sync back to JSON for consistency (optional, but good for persistence)
            # We won't write to disk on every read to save I/O, but we return the truth.
            
    except Exception as e:
        print(f"Error merging DB stats: {e}")
    finally:
        db.close()

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
        from core.network_utils import get_random_user_agent
        
        # [SYN-74] Assign a persistent User-Agent for this profile
        persistent_ua = get_random_user_agent()
        
        content_to_dump = cookies_data
        if isinstance(cookies_data, list):
             content_to_dump = {
                "cookies": cookies_data,
                "origins": [],
                "synapse_meta": {
                    "user_agent": persistent_ua
                }
            }
        elif isinstance(cookies_data, dict):
            # Ensure synapse_meta exists
            if "synapse_meta" not in content_to_dump:
                content_to_dump["synapse_meta"] = {}
            content_to_dump["synapse_meta"]["user_agent"] = persistent_ua
            
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
    from core.tiktok_profile import load_session_data, extract_cookies_dict, fetch_tiktok_user_info
    
    print(f"Starting metadata fetch for {profile_id}...")
    
    try:
        session_path = get_session_path(profile_id)
        if not os.path.exists(session_path):
            return

        data = load_session_data(session_path)
        if not data:
            return

        cookies = extract_cookies_dict(data)
        if not cookies:
            print(f"No cookies found for {profile_id}")
            return
            
        info = fetch_tiktok_user_info(cookies)
        
        if info:
            print(f"Metadata found: {info.get('display_name')}")
            update_profile_info(profile_id, {
                "username": info.get("unique_id") or info.get("username"), # username in endpoints.py is usually unique_id
                "label": info.get("display_name"), 
                "avatar_url": info.get("avatar_url")
            })
        else:
            print("Could not fetch metadata via API.")
            
    except Exception as e:
        print(f"Error fetching metadata for {profile_id}: {e}")

from datetime import datetime
from zoneinfo import ZoneInfo


@with_db_retries()
def update_profile_info(profile_id: str, info: Dict[str, Any]) -> bool:
    """
    Updates basic profile info (label, username, avatar) in SQLite.
    Includes retry logic for SQLite locking issues.
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
        if "active" in info:
            profile.active = info["active"]
        
        profile.updated_at = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@with_db_retries()
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

        profile.updated_at = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)

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
        profile.updated_at = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error updating status: {e}")
        return False
    finally:
        db.close()

def update_session_cookies(profile_id: str, cookies_json: str) -> bool:
    """
    Updates the cookies for an existing session/profile.
    """
    session_path = get_session_path(profile_id)
    if not os.path.exists(session_path):
        return False

    try:
        cookies_data = json.loads(cookies_json)
        
        # Sanitize cookies (Reusable logic from import_session)
        # TODO: Refactor import_session to use a shared sanitize function to avoid code duplication
        # For now, repeating the critical sanitization steps
        
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
                            cookie["sameSite"] = "Lax" # Default
                    else:
                        cookie["sameSite"] = "Lax"
                        
                    # Remove unsupported properties
                    for key in list(cookie.keys()):
                        if key not in ("name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"):
                            del cookie[key]
                    
                    if "expirationDate" in cookie:
                        cookie["expires"] = cookie.pop("expirationDate")

        # Load existing file to preserve other metadata if present
        with open(session_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)

        # [SYN-74] Ensure synapse_meta and User-Agent are preserved
        if isinstance(existing_data, dict):
            if "synapse_meta" not in existing_data:
                from core.network_utils import get_random_user_agent
                existing_data["synapse_meta"] = {"user_agent": get_random_user_agent()}
            elif "user_agent" not in existing_data["synapse_meta"]:
                from core.network_utils import get_random_user_agent
                existing_data["synapse_meta"]["user_agent"] = get_random_user_agent()
                 
            existing_data["cookies"] = cookies_data
        else:
            # Was a raw list, convert to dict to support metadata
            from core.network_utils import get_random_user_agent
            existing_data = {
                "cookies": cookies_data,
                "origins": [],
                "synapse_meta": {"user_agent": get_random_user_agent()}
            }
        
        # Save back
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2)

        # Update DB updated_at
        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(Profile.slug == profile_id).first()
            if profile:
                profile.updated_at = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
                profile.active = True
                
                # [SYN-FIX] Clear error screenshot on cookie renewal
                if profile.last_seo_audit:
                    current_audit = dict(profile.last_seo_audit)
                    if "last_error_screenshot" in current_audit:
                        del current_audit["last_error_screenshot"]
                        profile.last_seo_audit = current_audit
                
                db.commit()
        except:
            db.rollback()
        finally:
            db.close()
            
        return True

    except Exception as e:
        print(f"Error updating cookies for {profile_id}: {e}")
        return False
