import uuid
import json
import os
from datetime import datetime, timedelta
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
                
                event = {
                    "id": str(item.id), # Frontend expects string ID (legacy was uuid, DB is Integer usually, OR we can keep ID as string in model if we want? Model defined it as Integer. Frontend might break if it expects UUID string. Let's see.)
                    # Wait, Model defined id as Integer? `id = Column(Integer, primary_key=True)`
                    # Legacy used `str(uuid.uuid4())`.
                    # If I change ID to int, frontend `key={event.id}` is fine.
                    # BUT delete endpoint expects string? `event_id: str`. Int as string is fine.
                    
                    "profile_id": item.profile_slug,
                    "video_path": item.video_path,
                    "scheduled_time": item.scheduled_time.isoformat() if item.scheduled_time else None,
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

    def add_event(self, profile_id: str, video_path: str, scheduled_time: str, viral_music_enabled: bool = False, music_volume: float = 0.0, sound_id: str = None, sound_title: str = None) -> Dict:
        """Schedules a new video upload."""
        db = SessionLocal()
        try:
            # Parse time
            dt = datetime.fromisoformat(scheduled_time)
            
            # Pack extras into metadata
            meta = {
                "viral_music_enabled": viral_music_enabled,
                "music_volume": music_volume,
                "sound_id": sound_id,
                "sound_title": sound_title
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
                "scheduled_time": new_item.scheduled_time.isoformat(),
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
        try:
            try:
                pk = int(event_id)
            except ValueError:
                return False

            item = db.query(ScheduleItem).filter(ScheduleItem.id == pk).first()
            if item:
                item.scheduled_time = datetime.fromisoformat(scheduled_time)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"DB Error updating event: {e}")
            return False
        finally:
            db.close()

scheduler_service = Scheduler()
