from enum import Enum

class ScheduleStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    READY = "ready" # Intermediate state from uploader
    PAUSED_LOGIN_REQUIRED = "paused_login_required"
    SUCCESS = "success" # Intermediate state
