import uuid
import json
import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from core.database import SessionLocal
from core.models import ScheduleItem

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
                s_time = item.scheduled_time
                if s_time and s_time.tzinfo is None:
                    s_time = s_time.replace(tzinfo=timezone.utc)

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

    def add_event(self, profile_id: str, video_path: str, scheduled_time: str, viral_music_enabled: bool = False, music_volume: float = 0.0, sound_id: str = None, sound_title: str = None, smart_captions: bool = False) -> Dict:
        """Schedules a new video upload."""
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
                "smart_captions": smart_captions
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
                "scheduled_time": new_item.scheduled_time.replace(tzinfo=timezone.utc).isoformat() if new_item.scheduled_time.tzinfo is None else new_item.scheduled_time.isoformat(),
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

    def update_event(self, event_id: str, scheduled_time: str) -> bool:
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
                return True
            
            print(f"DEBUG: Item not found for id '{event_id}'")
            return False
        except Exception:
            db.rollback()
            raise  # Re-raise exception to be caught by API endpoint (500)
        finally:
            db.close()

    async def start_loop(self):
        """Starts the background scheduler loop."""
        print("[SCHEDULER] Loop Started...")
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
            now = datetime.now(timezone.utc)
            
            # Find due items
            # SQLite stores dates as naive strings mostly, or we handled it.
            # If we used timezone.utc in add_event, it stored ISO string with +00:00.
            # SQLAlchemy with SQLite might need careful comparison.
            # Let's fetch all pending and filter in python to be safe against SQLite timezone quirks, 
            # or rely on simple comparison if formats align.
            
            # Optimization: Filter roughly in SQL
            items = db.query(ScheduleItem).filter(
                ScheduleItem.status == 'pending',
                ScheduleItem.scheduled_time <= now
            ).all()
            
            for item in items:
                print(f"[SCHEDULER] Triggering due item {item.id} - {item.video_path}")
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
            # It usually moves file from approved/ -> processing/ -> done/
            # Here the file is likely in inputs/ or already in done/ if it was processed?
            # Wait, `video_path` in DB usually points to the file.
            # If it was uploaded via `scheduler/create`, where is the file?
            # It might be in `data/pending` or `data/library`.
            # We pass the absolute path.
            
            print(f"[SCHEDULER] Executing Video: {item.video_path}")
            
            # Need to ensure file exists
            if not os.path.exists(item.video_path):
                 print(f"[SCHEDULER] File not found: {item.video_path}")
                 item.status = 'failed'
                 # item.error_log = "File not found on disk" (No column)
                 print(f"Error Log: File not found on disk")
                 db.commit()
                 return

            # Call manual executor (which handles upload logic)
            # execute_approved_video is async
            result = await execute_approved_video(item.video_path, is_scheduled=True, metadata=item.metadata_info)
            
            if result.get('status') == 'success':
                item.status = 'completed'
                item.published_url = result.get('url')
            else:
                item.status = 'failed'
                # item.error_log = result.get('message')
                print(f"Error Log: {result.get('message')}")
            
            db.commit()
            
        except Exception as e:
            print(f"[SCHEDULER] Execution Failed: {e}")
            item.status = 'failed'
            # item.error_log = str(e)
            print(f"Error Log: {str(e)}")
            db.commit()

scheduler_service = Scheduler()
