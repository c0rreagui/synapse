
import asyncio
import os
import sys
# import pytest
# Mock Sentry before importing main
from unittest.mock import MagicMock
sys.modules["sentry_sdk"] = MagicMock()

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Setup Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from core.database import SessionLocal
from core.models import ScheduleItem

client = TestClient(app)

def test_upload_creates_db_record():
    # 1. Create Dummy Video
    dummy_filename = "test_trans_video.mp4"
    with open(dummy_filename, "wb") as f:
        f.write(b"dummy_content_transactional")
        
    try:
        # 2. Upload
        with open(dummy_filename, "rb") as f:
            response = client.post(
                "/api/v1/ingest/upload", 
                files={"file": (dummy_filename, f, "video/mp4")},
                data={"profile_id": "p1", "privacy_level": "public_to_everyone"}
            )
        
        # Check API success
        if response.status_code != 200:
            print(f"Upload failed: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 3. Verify DB Record Exists
        db = SessionLocal()
        try:
            # We expect a record with this filename (partially matched or tag matched)
            # The API returns the "filename" used (tagged_filename)
            tagged_name = data["filename"]
            
            item = db.query(ScheduleItem).filter(ScheduleItem.video_path == tagged_name).first()
            
            assert item is not None
            print(f"✅ DB Record Found: ID {item.id}, Status: {item.status}")
            
            # Initial status should be pending_analysis_oracle
            # But since background task runs immediately in TestClient (synchronously often in Starlette TestClient unless async?), 
            # or maybe not. 
            # TestClient runs background tasks? Yes usually.
            # So it might already be 'pending_approval' or 'failed_analysis' (due to missing dependencies in test env)
            
            print(f"Current Status: {item.status}")
            assert item.status in ["pending_analysis_oracle", "pending_approval", "failed_analysis"]
            
        finally:
            db.close()
            
    finally:
        if os.path.exists(dummy_filename):
            os.remove(dummy_filename)

if __name__ == "__main__":
    test_upload_creates_db_record()
