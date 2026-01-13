import json
import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta

SCHEDULE_FILE = "data/schedule.json"

class Scheduler:
    def __init__(self):
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)
        if not os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, 'w') as f:
                json.dump([], f)

    def load_schedule(self) -> List[Dict]:
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_schedule(self, data: List[Dict]):
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def add_event(self, profile_id: str, video_path: str, scheduled_time: str, viral_music_enabled: bool = False, music_volume: float = 0.0, trend_category: str = "General") -> Dict:
        """Schedules a new video upload."""
        events = self.load_schedule()
        event_id = str(uuid.uuid4())
        
        new_event = {
            "id": event_id,
            "profile_id": profile_id,
            "video_path": video_path,
            "scheduled_time": scheduled_time,
            "viral_music_enabled": viral_music_enabled,
            "music_volume": music_volume,
            "trend_category": trend_category,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        events.append(new_event)
        self.save_schedule(events)
        return new_event

    def delete_event(self, event_id: str) -> bool:
        events = self.load_schedule()
        initial_len = len(events)
        events = [e for e in events if e['id'] != event_id]
        if len(events) < initial_len:
            self.save_schedule(events)
            return True
        return False

    def is_slot_available(self, profile_id: str, check_time: datetime, buffer_minutes: int = 15) -> bool:
        """Checks if a time slot is free for a given profile within a buffer."""
        events = self.load_schedule()
        
        check_start = check_time - timedelta(minutes=buffer_minutes)
        check_end = check_time + timedelta(minutes=buffer_minutes)
        
        for event in events:
            if event['profile_id'] != profile_id:
                continue
                
            event_time = datetime.fromisoformat(event['scheduled_time'])
            # Naive comparison assuming both are same timezone logic
            if check_start < event_time < check_end:
                return False
                
        return True

    def find_next_available_slot(self, profile_id: str, start_time: datetime) -> str:
        """Finds the next available slot starting from start_time."""
        current_check = start_time
        
        # Safety limit to prevent infinite loops (e.g. max 1 week lookahead)
        max_attempts = 672 # 7 days * 24 hours * 4 slots/hour
        attempts = 0
        
        while attempts < max_attempts:
            if self.is_slot_available(profile_id, current_check):
                return current_check.isoformat()
            
            # Move forward by 15 minutes
            current_check += timedelta(minutes=15)
            attempts += 1
            
        # Fallback if really full (unlikely)
        return (start_time + timedelta(days=7)).isoformat()


    def update_event(self, event_id: str, scheduled_time: str) -> bool:
        events = self.load_schedule()
        for event in events:
            if event['id'] == event_id:
                event['scheduled_time'] = scheduled_time
                self.save_schedule(events)
                return True
        return False

scheduler_service = Scheduler()
