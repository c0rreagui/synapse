"""
Queue Management Endpoint - Manual Approval Workflow
Manages pending videos and approval flow
"""
import os
import json
import shutil
import asyncio
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")
APPROVED_DIR = os.path.join(BASE_DIR, "data", "approved")

# Ensure directories exist
os.makedirs(PENDING_DIR, exist_ok=True)
os.makedirs(APPROVED_DIR, exist_ok=True)


class PendingVideo(BaseModel):
    id: str
    filename: str
    profile: str
    uploaded_at: str
    status: str
    metadata: dict


class ApprovalRequest(BaseModel):
    id: str
    action: str  # "immediate" or "scheduled"
    schedule_time: Optional[str] = None


@router.get("/pending", response_model=List[PendingVideo])
async def get_pending_videos():
    """
    List all pending videos awaiting manual approval.
    """
    pending_videos = []
    
    try:
        if not os.path.exists(PENDING_DIR):
            return []
        
        # List all video files in pending
        for filename in os.listdir(PENDING_DIR):
            if not filename.endswith('.mp4'):
                continue
            
            # Extract ID from filename (format: profile_id.mp4)
            file_id = os.path.splitext(filename)[0]
            
            # Load metadata if exists
            metadata_path = os.path.join(PENDING_DIR, f"{filename}.json")
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            pending_videos.append(PendingVideo(
                id=file_id,
                filename=filename,
                profile=metadata.get('profile_id', 'unknown'),
                uploaded_at=metadata.get('uploaded_at', ''),
                status='pending',
                metadata=metadata
            ))
        
        return pending_videos
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing pending videos: {str(e)}")


@router.post("/approve")
async def approve_video(request: ApprovalRequest, background_tasks: BackgroundTasks):
    """
    Approve a pending video for processing.
    Moves from pending/ to approved/ and adds execution metadata.
    
    If action is 'immediate', triggers bot execution in background.
    """
    try:
        # Find video file
        video_filename = None
        for f in os.listdir(PENDING_DIR):
            if f.startswith(request.id) and f.endswith('.mp4'):
                video_filename = f
                break
        
        if not video_filename:
            raise HTTPException(status_code=404, detail=f"Video {request.id} not found in pending")
        
        # Paths
        pending_video = os.path.join(PENDING_DIR, video_filename)
        approved_video = os.path.join(APPROVED_DIR, video_filename)
        pending_metadata = os.path.join(PENDING_DIR, f"{video_filename}.json")
        approved_metadata = os.path.join(APPROVED_DIR, f"{video_filename}.json")
        
        # Load existing metadata
        metadata = {}
        if os.path.exists(pending_metadata):
            with open(pending_metadata, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        
        # Add approval info
        metadata['approved_at'] = datetime.now().isoformat()
        metadata['action'] = request.action
        metadata['schedule_time'] = request.schedule_time
        metadata['status'] = 'approved'
        
        # Move files
        shutil.move(pending_video, approved_video)
        
        # Save updated metadata
        with open(approved_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Remove old metadata if exists
        if os.path.exists(pending_metadata):
            os.remove(pending_metadata)
        
        # Trigger execution for immediate posts
        if request.action == 'immediate':
            # Import here to avoid circular dependency
            import sys
            import asyncio
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            from core.manual_executor import execute_approved_video
            
            # Create sync wrapper for background task
            def run_async_executor():
                """Wrapper to run async function in background task"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(execute_approved_video(video_filename))
                finally:
                    loop.close()
            
            # Add to background tasks (non-blocking)
            background_tasks.add_task(run_async_executor)
        
        return {
            "success": True,
            "message": f"Video approved for {request.action} processing",
            "filename": video_filename,
            "action": request.action,
            "schedule_time": request.schedule_time,
            "executing": request.action == 'immediate'
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving video: {str(e)}")


@router.delete("/{video_id}")
async def reject_video(video_id: str):
    """
    Reject a pending video (delete from pending).
    """
    try:
        # Find and delete video file
        deleted = False
        for filename in os.listdir(PENDING_DIR):
            if filename.startswith(video_id):
                file_path = os.path.join(PENDING_DIR, filename)
                os.remove(file_path)
                deleted = True
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        
        return {
            "success": True,
            "message": f"Video {video_id} rejected and removed"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting video: {str(e)}")
