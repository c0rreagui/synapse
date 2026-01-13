"""
Ingestion Endpoint - Receives video uploads from frontend
Saves files to inputs/ folder with profile tags for factory_watcher processing
"""
import os
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    profile_id: str = Form(...),
    caption: Optional[str] = Form(None),
    schedule_time: Optional[str] = Form(None),
    viral_music_enabled: bool = Form(False)
):
    """
    Upload a video file for automated processing.
    Now enriched with ORACLE content analysis in background.
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
            
        # Create Metadata JSON (Scheduling + Caption)
        import json
        metadata = {
            "caption": final_caption, # May be None, Oracle will fill it
            "schedule_time": schedule_time,
            "viral_music_enabled": viral_music_enabled,
            "original_filename": file.filename,
            "profile_id": profile_id,
            "uploaded_at": str(uuid.uuid1()),
            "oracle_status": "pending"
        }
        
        metadata_filename = f"{tagged_filename}.json"
        metadata_path = os.path.join(PENDING_DIR, metadata_filename)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        # 🟢 TRIGGER ORACLE IN BACKGROUND
        background_tasks.add_task(process_oracle_enrichment, metadata_path, file.filename, profile_id)
        
        return IngestResponse(
            success=True,
            message=f"Video queued. Oracle Analysis started in background.",
            file_id=file_id,
            filename=tagged_filename,
            profile=profile_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

# Background Task for Oracle
def process_oracle_enrichment(metadata_path: str, original_filename: str, profile_id: str):
    try:
        from core.oracle.seo_engine import seo_engine
        import json
        
        print(f"🔮 Oracle: Analyzing content for {original_filename}...")
        
        # 1. Generate Content Metadata
        # TODO: Get actual profile niche from Profile Metadata (omitted for speed, defaulting to 'General')
        analysis = seo_engine.generate_content_metadata(original_filename, niche="General")
        
        # 2. Update JSON
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update fields if clean (user didn't provide caption)
            if not data.get("caption"):
                data["caption"] = analysis.get("suggested_caption")
            
            data["oracle_analysis"] = analysis
            data["oracle_status"] = "completed"
            
            # 3. Smart Scheduling Suggestion (Mock for now, real implementation needs Scheduler Service)
            # data["suggested_time"] = ... 
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Oracle: Enrichment complete for {original_filename}")
            
    except Exception as e:
        print(f"❌ Oracle Background Error: {e}")


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
