from core.database import SessionLocal
from app.api.endpoints.clipper import list_clip_jobs

try:
    db = SessionLocal()
    result = list_clip_jobs(db)
    print("Success:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
