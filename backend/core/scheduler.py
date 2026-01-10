import json
import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime

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

    def add_event(self, profile_id: str, video_path: str, scheduled_time: str, viral_music_enabled: bool = False) -> Dict:
        """Schedules a new video upload."""
        events = self.load_schedule()
        event_id = str(uuid.uuid4())
        
        new_event = {
            "id": event_id,
            "profile_id": profile_id,
            "video_path": video_path,
            "scheduled_time": scheduled_time,
            "viral_music_enabled": viral_music_enabled,
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

scheduler_service = Scheduler()
