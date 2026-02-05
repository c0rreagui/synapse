import shutil
import os
import asyncio
import uuid
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional
from core.database import SessionLocal
from core.models import ScheduleItem
from core.logger import logger

# [SYN-FIX] Path Normalization: Docker <-> Windows
# When running locally on Windows, video_paths stored as Docker paths won't work.
# This function translates them to the correct local path.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
DATA_DIR = os.path.join(BASE_DIR, "data")

def normalize_video_path(docker_path: str) -> str:
    """
    Converts Docker-style paths (/app/data/...) to Windows paths.
    If already a Windows path, returns as-is.
    """
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
        pass

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
                    
                    # Unpack metadata
                    "viral_music_enabled": meta.get("viral_music_enabled", False),
                    "music_volume": meta.get("music_volume", 0.0),
                    "sound_id": meta.get("sound_id"),
                    "sound_title": meta.get("sound_title"),
                    "metadata": meta # Keep original metadata dict accessible if needed
                }
                results.append(event)
            return results
        except Exception as e:
            print(f"DB Error loading schedule: {e}")
            return []
        finally:
            db.close()

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

    def update_event(self, event_id: str, scheduled_time: str) -> Optional[Dict]:
        db = SessionLocal()
        print(f"DEBUG: update_event called for id='{event_id}'")
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
                # Safe Z handle
                clean_time = scheduled_time.replace("Z", "+00:00")
                item.scheduled_time = datetime.fromisoformat(clean_time)
                db.commit()
                db.refresh(item)
                
                return {
                    "id": str(item.id),
                    "profile_id": item.profile_slug,
                    "video_path": item.video_path,
                    "scheduled_time": item.scheduled_time.replace(tzinfo=ZoneInfo("America/Sao_Paulo")).isoformat() if item.scheduled_time.tzinfo is None else item.scheduled_time.isoformat(),
                    "viral_music_enabled": bool(item.metadata_info.get('viral_music_enabled', False)) if item.metadata_info else False,
                    "status": item.status,
                     # [SYN-FIX] Return all necessary fields for frontend
                }
            
            print(f"DEBUG: Item not found for id '{event_id}'")
            return None
        except Exception:
            db.rollback()
            raise  # Re-raise exception to be caught by API endpoint (500)
        finally:
            db.close()

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

    async def check_due_items(self):
        """Checks DB for pending items that are due."""
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
                logger.log("info", f"Found {len(due_items)} due items. Processing...", "scheduler")
            
            for item in due_items:
                logger.log("info", f"Triggering item {item.id} - {os.path.basename(item.video_path)}", "scheduler")
                # Execute Logic
                await self.execute_due_item(item, db)
                
        except Exception as e:
            print(f"Error checking due items: {e}")
        finally:
            db.close()

    async def execute_due_item(self, item: ScheduleItem, db):
        from core.manual_executor import execute_approved_video
        from core.status_manager import status_manager
        
        try:
            # 1. Update status to processing
            item.status = 'processing'
            db.commit()
            
            status_manager.update_status(
                state="busy",
                current_task=f"Scheduled: {os.path.basename(item.video_path)}",
                step="Executando Agendamento",
                progress=0
            )
            
            # 2. Execute
            # execute_approved_video expects a FILE PATH.
            # [SYN-FIX] Normalize Docker paths to Windows paths
            video_path = normalize_video_path(item.video_path)
            
            print(f"[SCHEDULER] Executing Video: {video_path}")
            
            # Need to ensure file exists
            if not os.path.exists(video_path):
                 print(f"[SCHEDULER] File not found: {video_path}")
                 item.status = 'failed'
                 print(f"Error Log: File not found on disk")
                 db.commit()
                 return

            # Call manual executor (which handles upload logic)
            # execute_approved_video is async
            
            # [SYN-FIX] Inject profile info into metadata so executor knows who to use
            exec_metadata = dict(item.metadata_info or {})
            exec_metadata['profile_slug'] = item.profile_slug
            exec_metadata['profile_id'] = item.profile_slug
            
            result = await execute_approved_video(video_path, is_scheduled=True, metadata=exec_metadata)
            
            if result.get('status') in ['success', 'ready', 'completed']:
                item.status = 'completed'
                item.published_url = result.get('url')
                logger.log("success", f"Successfully executed item {item.id} (Scheduled: {item.scheduled_time})", "scheduler")
            else:
                item.status = 'failed'
                # Save error to metadata for frontend display
                meta = dict(item.metadata_info or {})
                meta['error'] = result.get('message')
                item.metadata_info = meta
                
                print(f"Error Log: {result.get('message')}")
                logger.log("error", f"Failed to execute item {item.id}: {result.get('message')}", "scheduler")
            
            db.commit()
            
        except Exception as e:
            print(f"[SCHEDULER] Execution Failed: {e}")
            item.status = 'failed'
            
            meta = dict(item.metadata_info or {})
            meta['error'] = str(e)
            item.metadata_info = meta
            
            print(f"Error Log: {str(e)}")
            logger.log("error", f"Exception executing item {item.id}: {str(e)}", "scheduler")
            db.commit()

scheduler_service = Scheduler()
