from enum import Enum

class ScheduleStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    READY = "ready" # Intermediate state from uploader
    SUCCESS = "success" # Intermediate state
