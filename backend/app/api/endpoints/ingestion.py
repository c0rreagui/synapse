"""
Ingestion Endpoint - Receives video uploads from frontend
Saves files to inputs/ folder with profile tags for factory_watcher processing
"""
import os
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")

# Ensure pending directory exists
os.makedirs(PENDING_DIR, exist_ok=True)

class IngestResponse(BaseModel):
    success: bool
    message: str
    file_id: str
    filename: str
    profile: str


@router.post("/upload", response_model=IngestResponse)
async def upload_video(
    file: UploadFile = File(...),
    profile_id: str = Form(...),
    caption: Optional[str] = Form(None),
    schedule_time: Optional[str] = Form(None)
):
    """
    Upload a video file for automated processing.
    
    - **file**: Video file (mp4 recommended)
    - **profile_id**: Target profile (p1, p2, etc.)
    - **caption**: Optional caption for the video
    - **schedule_time**: Optional ISO datetime string for scheduling
    
    The file will be saved to inputs/ with a profile tag prefix,
    triggering the factory_watcher to process it automatically.
    """
    
    # Validate profile_id format
    if not profile_id.startswith("p"):
        profile_id = f"p{profile_id}"
    
    # Validate file type
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported: mp4, mov, avi, webm"
        )
    
    # Generate unique ID
    file_id = str(uuid.uuid4())[:8]
    
    # Build filename with profile tag: p1_abc123.mp4
    extension = os.path.splitext(file.filename)[1] or ".mp4"
    tagged_filename = f"{profile_id}_{file_id}{extension}"
    file_path = os.path.join(PENDING_DIR, tagged_filename)
    
    try:
        # Save the video file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Determine caption text
        final_caption = caption
        if not final_caption:
            final_caption = f"{os.path.splitext(file.filename)[0]} - Synapse Auto"
            
        # Create Metadata JSON (Scheduling + Caption)
        # This replaces the old simple .txt caption file
        import json
        metadata = {
            "caption": final_caption,
            "schedule_time": schedule_time, # ISO Format from frontend
            "original_filename": file.filename,
            "profile_id": profile_id,
            "uploaded_at": str(uuid.uuid1()) # Timestamp
        }
        
        metadata_filename = f"{tagged_filename}.json" # e.g. p1_xxx.mp4.json
        metadata_path = os.path.join(PENDING_DIR, metadata_filename)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return IngestResponse(
            success=True,
            message=f"Video queued for processing on profile {profile_id}. Scheduled: {schedule_time}",
            file_id=file_id,
            filename=tagged_filename,
            profile=profile_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )


@router.get("/status")
async def get_ingestion_status():
    """
    Get current ingestion queue status.
    Returns count of files in each processing stage.
    """
    processing_dir = os.path.join(BASE_DIR, "processing")
    done_dir = os.path.join(BASE_DIR, "done")
    errors_dir = os.path.join(BASE_DIR, "errors")
    
    def count_files(directory):
        if not os.path.exists(directory):
            return 0
        return len([f for f in os.listdir(directory) if f.endswith('.mp4')])
    
    return {
        "queued": count_files(PENDING_DIR),
        "processing": count_files(processing_dir),
        "completed": count_files(done_dir),
        "failed": count_files(errors_dir)
    }
