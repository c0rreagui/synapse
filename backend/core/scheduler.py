import shutil
import os
import asyncio
import uuid
import json
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional
from core.database import SessionLocal
from core.models import ScheduleItem
from core.logger import logger
from core.consts import ScheduleStatus
from core.database_utils import with_db_retries, retry_db_op
# [SYN-FIX] Path Normalization: Docker <-> Windows
# When running locally on Windows, video_paths stored as Docker paths won't work.
# This function translates them to the correct local path.
from core.config import DATA_DIR, BASE_DIR

def normalize_video_path(docker_path: str) -> str:
    """
    Normalizes video paths based on the current environment.
    - If running in Docker: keep Docker paths as-is
    - If running on Host: convert Docker paths to Windows paths
    """
    # Detect if we're running in Docker
    running_in_docker = os.path.exists("/.dockerenv")
    
    if running_in_docker:
        # We're in Docker, return path as-is
        return docker_path
    else:
        # We're on Host (Windows), convert Docker paths to Windows paths
        if docker_path.startswith("/app/data/"):
            # Extract relative path after /app/data/
            relative = docker_path.replace("/app/data/", "")
            return os.path.join(DATA_DIR, relative)
        elif docker_path.startswith("/app/"):
            # Other /app/ paths
            relative = docker_path.replace("/app/", "")
            return os.path.join(BASE_DIR, relative)
        else:
            # Already a Windows path or other
            return docker_path

class Scheduler:
    def __init__(self):
        # Database is auto-initialized by core.database
        self.semaphore = asyncio.Semaphore(1) # [SYN-FIX] Limit to 1 concurrent upload to save RAM


    @with_db_retries()
    def load_schedule(self) -> List[Dict]:
        """Loads all schedule items from DB and formats them as dicts."""
        db = SessionLocal()
        try:
            items = db.query(ScheduleItem).all()
            results = []
            for item in items:
                # Convert DB model to Dictionary expected by Frontend
                # We unpack metadata_info back to top level for compatibility
                meta = item.metadata_info if item.metadata_info else {}
                
                # Ensure we return UTC-aware string so frontend converts to Local correctly
                # Ensure we return Aware string (Sao Paulo)
                s_time = item.scheduled_time
                if s_time and s_time.tzinfo is None:
                    # [SYN-FIX] Naive in DB = Sao Paulo Time (User Local)
                    # Previously was timezone.utc, which caused 15:00 -> 12:00 shift
                    s_time = s_time.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))

                event = {
                    "id": str(item.id),
                    "profile_id": item.profile_slug,
                    "video_path": item.video_path,
                    "scheduled_time": s_time.isoformat() if s_time else None,
                    "status": item.status,
                    "error_message": item.error_message,
                    
                    # Unpack metadata
                    "viral_music_enabled": meta.get("viral_music_enabled", False),
                    "music_volume": meta.get("music_volume", 0.0),
                    "sound_id": meta.get("sound_id"),
                    "sound_title": meta.get("sound_title"),
                    "caption": meta.get("caption", ""),
                    "privacy_level": meta.get("privacy_level", "public"),
                    "metadata": meta
                }
                results.append(event)
            return results
        except Exception as e:
            print(f"DB Error loading schedule: {e}")
            return []
        finally:
            db.close()

    @with_db_retries()
    def add_event(self, profile_id: str, video_path: str, scheduled_time: str, viral_music_enabled: bool = False, music_volume: float = 0.0, sound_id: str = None, sound_title: str = None, smart_captions: bool = False, privacy_level: str = "public", caption: str = None) -> Dict:
        """Schedules a new video upload."""
        
        # [SYN-FIX] Auto-move from Pending -> Approved
        # If the video is in 'pending', we must move it to 'approved' so it leaves the Approval Queue.
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")
            APPROVED_DIR = os.path.join(BASE_DIR, "data", "approved")
            os.makedirs(APPROVED_DIR, exist_ok=True)
            
            # Normalize paths for comparison
            abs_video_path = os.path.abspath(video_path)
            abs_pending_dir = os.path.abspath(PENDING_DIR)
            
            # Check if file is inside PENDING_DIR
            if os.path.commonpath([abs_video_path, abs_pending_dir]) == abs_pending_dir and os.path.exists(abs_video_path):
                filename = os.path.basename(video_path)
                new_path = os.path.join(APPROVED_DIR, filename)
                
                # Move file
                shutil.move(abs_video_path, new_path)
                print(f"[SCHEDULER] Moved scheduled file to approved: {filename}")
                
                # Update path variable for DB
                video_path = new_path
                
                # Also move metadata if exists
                meta_src = os.path.join(PENDING_DIR, f"{filename}.json")
                if os.path.exists(meta_src):
                    meta_dst = os.path.join(APPROVED_DIR, f"{filename}.json")
                    shutil.move(meta_src, meta_dst)
                    
        except Exception as e:
            print(f"[SCHEDULER] Warning during file move: {e}")
            # Continue anyway, don't block scheduling
            
        db = SessionLocal()
        try:
            # Parse time (Safe Z handle)
            clean_time = scheduled_time.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_time)
            
            # Pack extras into metadata
            meta = {
                "viral_music_enabled": viral_music_enabled,
                "music_volume": music_volume,
                "sound_id": sound_id,
                "sound_title": sound_title,
                "smart_captions": smart_captions,
                "privacy_level": privacy_level,
                "caption": caption
            }
            
            # Race Condition Check: Prevent duplicate scheduling for same video/time
            existing = db.query(ScheduleItem).filter(
                ScheduleItem.profile_slug == profile_id,
                ScheduleItem.video_path == video_path,
                ScheduleItem.status == 'pending'
            ).first()
            
            if existing:
                # If exact duplicate exists, return it instead of creating new
                # This prevents double-clicks from creating two items
                print(f"Duplicate schedule detected for {video_path}, returning existing.")
                return {
                    "id": str(existing.id),
                    "profile_id": existing.profile_slug,
                    "video_path": existing.video_path,
                    "scheduled_time": existing.scheduled_time.isoformat() if existing.scheduled_time else None,
                    "status": existing.status,
                    "message": "Duplicate detected, returned existing item."
                }

            new_item = ScheduleItem(
                profile_slug=profile_id,
                video_path=video_path,
                scheduled_time=dt,
                status="pending",
                metadata_info=meta
            )
            
            db.add(new_item)
            db.commit()
            db.refresh(new_item)
            
            # Return dict format
            return {
                "id": str(new_item.id),
                "profile_id": new_item.profile_slug,
                "video_path": new_item.video_path,
                "scheduled_time": new_item.scheduled_time.replace(tzinfo=ZoneInfo("America/Sao_Paulo")).isoformat() if new_item.scheduled_time.tzinfo is None else new_item.scheduled_time.isoformat(),
                "viral_music_enabled": viral_music_enabled,
                "music_volume": music_volume,
                "sound_id": sound_id,
                "sound_title": sound_title,
                "status": new_item.status,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            db.rollback()
            print(f"DB Error adding event: {e}")
            raise e
        finally:
            db.close()

    @with_db_retries()
    def delete_event(self, event_id: str) -> bool:
        db = SessionLocal()
        try:
            # Try to find by ID (Integer)
            # Incoming event_id might be string "1".
            try:
                pk = int(event_id)
            except ValueError:
                # If it's a legacy UUID string, we won't find it in new DB integer column.
                return False
                
            item = db.query(ScheduleItem).filter(ScheduleItem.id == pk).first()
            if item:
                db.delete(item)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"DB Error deleting event: {e}")
            return False
        finally:
            db.close()
            
    @with_db_retries()
    def cleanup_missed_schedules(self):
        """
        [SYN-42] Lifecycle Management:
        Checks for 'pending' events that are significantly past their due date (e.g. > 1h).
        Marks them as 'failed' or 'expired' so they don't clog the 'Up Next' list.
        """
        db = SessionLocal()
        try:
            # Threshold: 1 hour past due
            # [SYN-FIX] Use SP Time for threshold (DB stores local time)
            sp_tz = ZoneInfo("America/Sao_Paulo")
            now_sp = datetime.now(sp_tz).replace(tzinfo=None) # Make naive for comparison with DB
            threshold = now_sp - timedelta(hours=1)
            
            # Find expired pending items (using loose slug match or status)
            expired_items = db.query(ScheduleItem).filter(
                ScheduleItem.status == "pending",
                ScheduleItem.scheduled_time < threshold
            ).all()
            
            if expired_items:
                count = 0
                for item in expired_items:
                    print(f"[SCHEDULER] Expired item detected: {item.id} (Due: {item.scheduled_time})")
                    item.status = "failed"
                    # Add metadata explanation
                    current_meta = item.metadata_info or {}
                    current_meta["error"] = "Schedule expired (Missed window by >1h)"
                    item.metadata_info = current_meta
                    count += 1
                
                db.commit()
                if count > 0:
                    print(f"[SCHEDULER] Cleaned up {count} expired schedule items.")
                    
        except Exception as e:
            print(f"[SCHEDULER] Error cleaning up missed schedules: {e}")
            db.rollback()
        finally:
            db.close()

    @with_db_retries()
    def cleanup_phantom_events(self):
        """Removes any events associated with phantom/temporary profile IDs."""
        db = SessionLocal()
        try:
            deleted = db.query(ScheduleItem).filter(
                ScheduleItem.profile_slug.like("ptiktok_%")
            ).delete(synchronize_session=False)
            
            if deleted > 0:
                print(f"[SCHEDULER] Cleaned up {deleted} phantom events")
                db.commit()
        except Exception as e:
            print(f"[SCHEDULER] Cleanup error: {e}")
            db.rollback()
        finally:
            db.close()

    @with_db_retries()
    def is_slot_available(self, profile_id: str, check_time: datetime, buffer_minutes: int = 15) -> bool:
        """Checks if a time slot is free for a given profile within a buffer."""
        db = SessionLocal()
        try:
            check_start = check_time - timedelta(minutes=buffer_minutes)
            check_end = check_time + timedelta(minutes=buffer_minutes)
            
            # Query for overlap
            # We want count of events for this profile in range
            count = db.query(ScheduleItem).filter(
                ScheduleItem.profile_slug == profile_id,
                ScheduleItem.scheduled_time > check_start,
                ScheduleItem.scheduled_time < check_end
            ).count()
            
            return count == 0
        except Exception as e:
            print(f"DB Error checking slot: {e}")
            return False # Fail safe? Or True? False prevents overlap.
        finally:
            db.close()

    def find_next_available_slot(self, profile_id: str, start_time: datetime) -> str:
        """Finds the next available slot starting from start_time."""
        current_check = start_time
        
        # Optimization: Instead of 600 queries, we could fetch all future events once.
        # But for 'find next', usually it's close.
        
        max_attempts = 672 # 7 days
        attempts = 0
        
        while attempts < max_attempts:
            if self.is_slot_available(profile_id, current_check):
                return current_check.isoformat()
            
            # Move forward by 15 minutes
            current_check += timedelta(minutes=15)
            attempts += 1
            
        return (start_time + timedelta(days=7)).isoformat()

    @with_db_retries()
    def update_event(self, event_id: str, scheduled_time: str = None, **kwargs) -> Optional[Dict]:
        """
        [SYN-EDIT] Full Edit Support.
        Updates any combination of: scheduled_time, profile_id, caption, privacy_level,
        viral_music_enabled, music_volume.
        """
        db = SessionLocal()
        print(f"DEBUG: update_event called for id='{event_id}', kwargs={kwargs}")
        try:
            # Try to handle both Integer (new) and String/UUID (legacy) IDs
            item = None
            
            # First try as integer
            try:
                pk = int(event_id)
                item = db.query(ScheduleItem).filter(ScheduleItem.id == pk).first()
            except ValueError:
                pass
            
            if not item:
                # Fallback to string search
                print(f"DEBUG: searching as string '{event_id}'")
                item = db.query(ScheduleItem).filter(ScheduleItem.id == event_id).first()
            
            if item:
                print(f"DEBUG: found item {item.id}, updating...")

                # --- Update Scheduled Time (if provided) ---
                if scheduled_time:
                    clean_time = scheduled_time.replace("Z", "+00:00")
                    dt_obj = datetime.fromisoformat(clean_time)

                    # [SYN-FIX] Timezone Correction
                    sp_tz = ZoneInfo("America/Sao_Paulo")
                    if dt_obj.tzinfo is not None:
                        dt_sp = dt_obj.astimezone(sp_tz)
                        item.scheduled_time = dt_sp.replace(tzinfo=None)
                    else:
                        item.scheduled_time = dt_obj
                    
                    # [SYN-FIX] Force status reset to pending if time changes
                    # This ensures the scheduler picks it up again (e.g. from failed -> pending)
                    if item.status != 'processing':
                        print(f"DEBUG: Reschedule detected. Resetting status {item.status} -> pending")
                        item.status = 'pending'
                        item.error_message = None

                # --- Update Profile (if provided) ---
                if 'profile_id' in kwargs and kwargs['profile_id'] is not None:
                    item.profile_slug = kwargs['profile_id']

                # --- Update Metadata Fields ---
                meta = dict(item.metadata_info) if item.metadata_info else {}
                metadata_fields = ['caption', 'privacy_level', 'viral_music_enabled', 'music_volume']
                for field in metadata_fields:
                    if field in kwargs and kwargs[field] is not None:
                        meta[field] = kwargs[field]
                item.metadata_info = meta

                db.commit()
                db.refresh(item)
                
                # Build enriched response
                refreshed_meta = item.metadata_info or {}
                
                # Format time logic
                s_time_formatted = None
                if item.scheduled_time:
                    if item.scheduled_time.tzinfo is None:
                        s_time_formatted = item.scheduled_time.replace(tzinfo=ZoneInfo("America/Sao_Paulo")).isoformat()
                    else:
                        s_time_formatted = item.scheduled_time.isoformat()

                return {
                    "id": str(item.id),
                    "profile_id": item.profile_slug,
                    "video_path": item.video_path,
                    "scheduled_time": s_time_formatted,
                    "status": item.status,
                    "error_message": item.error_message,
                    "viral_music_enabled": bool(refreshed_meta.get('viral_music_enabled', False)),
                    "music_volume": refreshed_meta.get('music_volume', 0.0),
                    "sound_id": refreshed_meta.get('sound_id'),
                    "sound_title": refreshed_meta.get('sound_title'),
                    "caption": refreshed_meta.get('caption', ''),
                    "privacy_level": refreshed_meta.get('privacy_level', 'public'),
                    "metadata": refreshed_meta,
                }
            
            print(f"DEBUG: Item not found for id '{event_id}'")
            return None
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @with_db_retries()
    def update_video_path(self, old_path: str, new_path: str) -> int:
        """Updates the video path for all pending/scheduled items."""
        db = SessionLocal()
        try:
            # Find items with old path
            items = db.query(ScheduleItem).filter(ScheduleItem.video_path == old_path).all()
            count = 0
            for item in items:
                item.video_path = new_path
                count += 1
            
            if count > 0:
                print(f"[SCHEDULER] Updated path for {count} items: {old_path} -> {new_path}")
                db.commit()
            return count
        except Exception as e:
            db.rollback()
            print(f"DB Error updating video path: {e}")
            return 0
        finally:
            db.close()

    async def start_loop(self):
        """Starts the background scheduler loop."""
        print("[SCHEDULER] Loop Started...")
        
        # [SYN-FIX] Run cleanup on startup
        self.cleanup_phantom_events()
        
        while True:
            try:
                await self.check_due_items()
            except Exception as e:
                print(f"Scheduler Loop Error: {e}")
            await asyncio.sleep(60) # Check every minute

    @with_db_retries()
    async def check_due_items(self):
        """Checks DB for pending items that are due."""
        # 💓 [NEW] Post Heartbeat for System Sonar
        # ... (heartbeat code if exists)
        
        # 🛡️ CIRCUIT BREAKER CHECK
        from core.circuit_breaker import circuit_breaker
        if circuit_breaker.is_open():
             # Only log once per minute to avoid spam, or reliance on logger level
             print("[PAUSED] Scheduler Paused: Circuit Breaker is OPEN.")
             return
             
        try:
            hb_path = os.path.join(DATA_DIR, "scheduler_heartbeat.json")
            with open(hb_path, 'w') as f:
                json.dump({
                    "timestamp": time.time(),
                    "last_beat": datetime.now().isoformat(),
                    "pid": os.getpid()
                }, f)
        except Exception as e:
            print(f"Error writing heartbeat: {e}")

        db = SessionLocal()
        try:
            # [SYN-FIX] Standardize on America/Sao_Paulo (User Request)
            sp_tz = ZoneInfo("America/Sao_Paulo")
            now = datetime.now(sp_tz)
            
            # Fetching pending items to handle TZ normalization in Python for SQLite safety
            pending_items = db.query(ScheduleItem).filter(
                ScheduleItem.status == 'pending'
            ).all()
            
            due_items = []
            for item in pending_items:
                s_time = item.scheduled_time
                if not s_time:
                    continue
                
                # Normalize item time to SP
                if s_time.tzinfo is None:
                    # If naive, assume SP (Standardized)
                    s_time = s_time.replace(tzinfo=sp_tz)
                else:
                    # Convert to SP
                    s_time = s_time.astimezone(sp_tz)
                
                if s_time <= now:
                    due_items.append(item)
                    print(f"[SCHEDULER] Found Due Item {item.id}: {s_time} <= {now}")

            if due_items:
                logger.log("info", f"Found {len(due_items)} due items. Processing concurrently...", "scheduler")
            
                # [SYN-FIX] Concurrent Execution (asyncio.gather)
                # This fixes the bug where items were processed sequentially or loop was broken
                # [SYN-FIX] Semaphore-controlled concurrency
                # We iterate and acquire semaphore for each task, or just run them sequentially for safety.
                # Given the machine freeze, let's process SEQUENTIALLY for now or use the semaphore.
                
                for item in due_items:
                    async with self.semaphore:
                        logger.log("info", f"Triggering item {item.id}", "scheduler")
                        await self.execute_due_item(item, db)

            # Since check_due_items runs every minute, we can do a quick check here.
            # [SYN-FIX] Use SP Time for threshold to match DB storage (Naive = SP)
            now_sp = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
            zombie_threshold = now_sp - timedelta(hours=1)
            print(f"[DEBUG] Zombie Check: NowSP={now_sp}, Threshold={zombie_threshold}")
            zombies = db.query(ScheduleItem).filter(
                ScheduleItem.status == 'processing',
                ScheduleItem.scheduled_time < zombie_threshold
            ).all()
            if zombies:
                 print(f"[DEBUG] Found Zombies: {[z.id for z in zombies]}")
            
            for zombie in zombies:
                logger.log("warning", f"Zombie detected: Item {zombie.id} stuck in processing. Marking as failed.", "scheduler")
                zombie.status = 'failed'
                zombie.error_message = "ZOMBIE HOST DETECTED: Pipeline stuck for >1h"
            
            if zombies:
                db.commit()

            # Heartbeat (Sonar)
            self._update_heartbeat()
                
        except Exception as e:
            print(f"Error checking due items: {e}")
        finally:
            db.close()

    def _update_heartbeat(self):
        """Updates the heartbeat file for Sonar monitoring."""
        try:
            hb_path = os.path.join(DATA_DIR, "scheduler_heartbeat.json")
            data = {
                "status": "running",
                "last_beat": datetime.now(timezone.utc).isoformat(),
                "pid": os.getpid(),
                "timestamp": time.time()
            }
            # Atomic write pattern to avoid partial reads
            tmp_path = hb_path + ".tmp"
            with open(tmp_path, 'w') as f:
                json.dump(data, f)
            os.replace(tmp_path, hb_path)
        except Exception as e:
            logger.log("error", f"[SONAR] Failed to update heartbeat: {e}", "scheduler")

    @with_db_retries()
    async def _claim_scheduled_item(self, item_id: int, new_status: str = 'processing') -> bool:
        """
        Atomically tries to claim an item by setting status to new_status (default 'processing').
        Returns True if successful, False if race condition lost.
        """
        db = SessionLocal()
        try:
            result = db.query(ScheduleItem).filter(
                ScheduleItem.id == item_id,
                ScheduleItem.status == 'pending'
            ).update({"status": new_status}, synchronize_session=False)
            db.commit()
            return result > 0
        finally:
            db.close()

    @with_db_retries()
    async def _finalize_scheduled_item(self, item_id: int, status: str, result: Dict):
        """Finalizes item status to COMPLETED or FAILED."""
        db = SessionLocal()
        try:
            item = db.query(ScheduleItem).filter(ScheduleItem.id == item_id).first()
            if not item: return

            item.status = status
            item.error_message = result.get('message')
            if status == ScheduleStatus.COMPLETED:
                item.published_url = result.get('url')
                item.error_message = None
                from core.session_manager import update_profile_metadata
                update_profile_metadata(item.profile_slug, {"last_error_screenshot": None})
            else:
                 # fallback metadata
                 meta = dict(item.metadata_info or {})
                 meta['error'] = result.get('message')
                 item.metadata_info = meta

            db.commit()
        finally:
            db.close()

    async def execute_due_item(self, item: ScheduleItem, db):
        from core.queue_manager import QueueManager
        from core.consts import ScheduleStatus
        from core.session_manager import get_profile_user_agent, get_session_path, check_cookies_validity

        try:
            # 0. Lightweight Pre-flight: Check if cookies exist and are not expired
            print(f"[SCHEDULER] Running lightweight cookie check for {item.profile_slug}...")
            session_file = get_session_path(item.profile_slug)
            
            # Helper to fail quickly
            async def fail_preflight(msg):
                print(f"[SCHEDULER] Pre-flight failed: {msg}")
                await self._finalize_scheduled_item(
                    item.id, 
                    ScheduleStatus.PAUSED_LOGIN_REQUIRED, 
                    {"message": msg}
                )

            if not os.path.exists(session_file):
                await fail_preflight("Session file not found")
                return

            try:
                with open(session_file, 'r', encoding='utf-8') as _f:
                    _data = json.load(_f)
                    _cookies = _data.get("cookies", []) if isinstance(_data, dict) else _data
                if not check_cookies_validity(_cookies):
                    await fail_preflight("Session cookies expired (pre-flight)")
                    return
                print(f"[SCHEDULER] Cookie check passed for {item.profile_slug}")
            except Exception as cookie_err:
                print(f"[SCHEDULER] Cookie check error (proceeding anyway): {cookie_err}")

            # 1. Update status to QUEUED (ATOMIC CHECK-AND-SET)
            # We claim it by moving to QUEUED state.
            acquired = await self._claim_scheduled_item(item.id, new_status=ScheduleStatus.QUEUED)
            if not acquired:
                print(f"[SCHEDULER] Race condition detected: Item {item.id} already claimed.")
                return

            print(f"[SCHEDULER] Acquired lock for item {item.id} -> QUEUED")
            
            # 2. Enqueue Job
            video_path = normalize_video_path(item.video_path)
            
            # Prepare metadata
            exec_metadata = dict(item.metadata_info or {})
            exec_metadata['profile_slug'] = item.profile_slug
            exec_metadata['profile_id'] = item.profile_slug
            exec_metadata['user_agent'] = get_profile_user_agent(item.profile_slug)
            
            try:
                job_id = await QueueManager.enqueue_upload(item.id, video_path, exec_metadata)
                print(f"[SCHEDULER] Item {item.id} pushed to Redis Queue: Job {job_id}")
            except Exception as queue_err:
                print(f"[SCHEDULER] Failed to enqueue item {item.id}: {queue_err}")
                # Rollback status to failed (or pending retry?)
                await self._finalize_scheduled_item(item.id, ScheduleStatus.FAILED, {"message": f"Queue Error: {queue_err}"})
                
        except Exception as e:
            print(f"[{ScheduleStatus.FAILED.upper()}] Scheduler Enqueue Failed: {e}")
            logger.log("error", f"Exception queuing item {item.id}: {str(e)}", "scheduler")
            try:
                await self._finalize_scheduled_item(item.id, ScheduleStatus.FAILED, {"message": str(e)})
            except:
                pass


    @with_db_retries()
    def retry_event(self, event_id: str, mode: str = "now") -> Dict:
        """
        Retries a failed event by restoring the file and resetting status.
        mode: "now" (immediate) or "next_slot" (tomorrow + same time)
        """
        db = SessionLocal()
        try:
            # 1. Find Event
            item = None
            try:
                pk = int(event_id)
                item = db.query(ScheduleItem).filter(ScheduleItem.id == pk).first()
            except ValueError:
                pass
            
            if not item:
                # Fallback to string search
                item = db.query(ScheduleItem).filter(ScheduleItem.id == event_id).first()

            if not item:
                 raise ValueError("Event not found")

            # 2. Locate and Restore File
            # Config imports here to avoid circulars if any, but config is safe
            from core.config import APPROVED_DIR, ERRORS_DIR, PROCESSING_DIR, DONE_DIR, DATA_DIR
            
            current_path = item.video_path
            filename = os.path.basename(current_path)
            
            # Define all possible locations where video might be
            PENDING_DIR = os.path.join(DATA_DIR, "pending")
            search_locations = [
                current_path,  # Original path
                os.path.join(APPROVED_DIR, filename),
                os.path.join(ERRORS_DIR, filename),
                os.path.join(PROCESSING_DIR, filename),
                os.path.join(DONE_DIR, filename),
                os.path.join(PENDING_DIR, filename),
            ]
            
            found_path = None
            
            for location in search_locations:
                if os.path.exists(location):
                    found_path = location
                    print(f"[RETRY] Found video at: {location}")
                    break
                    
            if not found_path:
                # [SYN-FIX] Fallback: Search by partial match (hash suffix)
                # Files may have numeric prefixes like "18_ptiktok_profile_..." 
                import glob
                # Extract the unique hash from filename (last part before extension)
                name_no_ext = os.path.splitext(filename)[0]
                ext = os.path.splitext(filename)[1]
                # Try matching by the last segment (hash) which is unique
                parts = name_no_ext.split('_')
                if len(parts) >= 2:
                    hash_suffix = parts[-1]  # e.g. "39e73118"
                    for search_dir in [APPROVED_DIR, ERRORS_DIR, PROCESSING_DIR, DONE_DIR, PENDING_DIR]:
                        if os.path.isdir(search_dir):
                            matches = glob.glob(os.path.join(search_dir, f"*{hash_suffix}{ext}"))
                            if matches:
                                found_path = matches[0]
                                print(f"[RETRY] Found video via hash match: {found_path}")
                                break
                
            if not found_path:
                locations_checked = [os.path.basename(os.path.dirname(l)) or "root" for l in search_locations]
                print(f"[RETRY] Critical: File {filename} not found. Checked: {locations_checked}")
                raise FileNotFoundError(f"Video file '{filename}' is missing from disk. Checked: approved, errors, processing, done, pending.")
                    
            # Restore to PENDING_DIR to avoid QueueWorker stealing the task
            # [SYN-FIX] Race Condition: QueueWorker monitors 'approved', so we use 'pending'
            if not os.path.exists(PENDING_DIR):
                os.makedirs(PENDING_DIR)
                
            restore_path = os.path.join(PENDING_DIR, filename)
            
            # If found_path is different from restore_path, move it
            if os.path.abspath(found_path) != os.path.abspath(restore_path):
                # Ensure destination doesn't exist (overwrite?)
                if os.path.exists(restore_path):
                     # If conflicting file exists, rename incoming
                     name, ext = os.path.splitext(filename)
                     new_name = f"{name}_retry_{int(time.time())}{ext}"
                     restore_path = os.path.join(PENDING_DIR, new_name)
                     
                shutil.move(found_path, restore_path)
                print(f"[RETRY] Restored file from {found_path} -> {restore_path}")
                item.video_path = restore_path
            
            # 3. Scheduling Logic
            if mode == "next_slot":
                # [SYN-FIX] Find the first DAY with NO scheduled posts for this profile
                # Instead of just adding 1 day, find a truly empty day
                sp_tz = ZoneInfo("America/Sao_Paulo")
                current_sched = item.scheduled_time
                if current_sched.tzinfo is None:
                    current_sched = current_sched.replace(tzinfo=sp_tz)
                else:
                    current_sched = current_sched.astimezone(sp_tz)
                
                # Get the TIME (hour/minute) from original schedule
                original_hour = current_sched.hour
                original_minute = current_sched.minute
                
                # Start looking from tomorrow
                from datetime import date
                check_date = (current_sched + timedelta(days=1)).date()
                max_days = 60  # Look up to 60 days ahead
                
                # Query all future events for this profile
                future_events = db.query(ScheduleItem).filter(
                    ScheduleItem.profile_slug == item.profile_slug,
                    ScheduleItem.scheduled_time >= datetime.now(sp_tz).replace(tzinfo=None),
                    ScheduleItem.status.in_(['pending', 'processing'])
                ).all()
                
                # Build set of dates that have events
                busy_dates = set()
                for evt in future_events:
                    if evt.scheduled_time:
                        evt_dt = evt.scheduled_time
                        if evt_dt.tzinfo is None:
                            evt_dt = evt_dt.replace(tzinfo=sp_tz)
                        busy_dates.add(evt_dt.date())
                
                # Find first empty day
                found_empty_day = None
                for days_ahead in range(max_days):
                    candidate_date = check_date + timedelta(days=days_ahead)
                    if candidate_date not in busy_dates:
                        found_empty_day = candidate_date
                        break
                
                if not found_empty_day:
                    # Fallback: use day after all events
                    found_empty_day = check_date + timedelta(days=max_days)
                
                # Combine found day with original time
                new_datetime = datetime(
                    found_empty_day.year,
                    found_empty_day.month,
                    found_empty_day.day,
                    original_hour,
                    original_minute,
                    tzinfo=sp_tz
                )
                
                item.scheduled_time = new_datetime.replace(tzinfo=None)  # Store as naive (SP assumed)
                print(f"[RETRY] Rescheduled from {current_sched.date()} to {found_empty_day} (first empty day)")
                
            elif mode == "now":
                # [SYN-FIX] Execute immediately instead of waiting for scheduler
                # Update scheduled_time to now so it shows correctly in UI
                sp_tz = ZoneInfo("America/Sao_Paulo")
                item.scheduled_time = datetime.now(sp_tz).replace(tzinfo=None)
            
            # 4. Reset Status
            item.status = "pending"
            item.error_message = None
            
            # Clear error in metadata too
            if item.metadata_info:
                meta = dict(item.metadata_info)
                if "error" in meta:
                    del meta["error"]
                item.metadata_info = meta

            db.commit()
            db.refresh(item)
            
            # [SYN-FIX] For "now" mode, trigger immediate execution in background
            if mode == "now":
                import asyncio
                import threading
                item_id = item.id  # Capture ID before db closes
                print(f"[RETRY] Triggering immediate execution for item {item_id}")
                
                async def execute_single_item(event_id):
                    """Wrapper to execute a single item by ID with its own DB session"""
                    # Wait a moment for the commit to be visible to other sessions
                    await asyncio.sleep(0.5)
                    
                    exec_db = SessionLocal()
                    try:
                        print(f"[RETRY_WORKER] Starting execution for {event_id}...")
                        exec_item = exec_db.query(ScheduleItem).filter(ScheduleItem.id == event_id).first()
                        if exec_item:
                            if exec_item.status == 'pending':
                                await self.execute_due_item(exec_item, exec_db)
                            else:
                                print(f"[RETRY_WORKER] Item {event_id} is not pending (status={exec_item.status}). usage skipped.")
                        else:
                             print(f"[RETRY_WORKER] Item {event_id} not found in worker session.")
                    except Exception as ex:
                        print(f"[RETRY] Execution failed: {ex}")
                        import traceback
                        traceback.print_exc()
                    finally:
                        exec_db.close()
                
                # Robust Async Trigger
                try:
                    # 1. Try to get the running loop (FastAPI main loop)
                    loop = asyncio.get_running_loop()
                    loop.create_task(execute_single_item(item_id))
                    print(f"[RETRY] Task created in running loop.")
                except RuntimeError:
                    # 2. No running loop (e.g. called from synchronous context or thread), start a new one in a thread
                    print(f"[RETRY] No running loop, spawning thread...")
                    def run_execution():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(execute_single_item(item_id))
                        new_loop.close()
                        
                    thread = threading.Thread(target=run_execution, daemon=True)
                    thread.start()
            
            return {
                "success": True,
                "new_status": item.status,
                "new_time": item.scheduled_time.isoformat(),
                "message": f"Retried successfully (Mode: {mode})" + (" - Executing now!" if mode == "now" else "")
            }

        except Exception as e:
            db.rollback()
            print(f"[RETRY] Error: {e}")
            raise e
        finally:
            db.close()

scheduler_service = Scheduler()
