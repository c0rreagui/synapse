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

from .. import websocket

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
    target_profile_id: Optional[str] = None  # Override profile for this video
    viral_music_enabled: bool = False  # Feature: Add viral music (muted)
    privacy_level: str = "public_to_everyone"  # Feature: Privacy (public_to_everyone, mutual_follow_friends, self_only)
    caption: Optional[str] = None  # Feature: Edit caption during approval


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
        metadata['viral_music_enabled'] = request.viral_music_enabled
        metadata['privacy_level'] = request.privacy_level
        
        # Update caption if provided
        if request.caption:
            metadata['caption'] = request.caption
        
        # Override profile if provided
        if request.target_profile_id:
            metadata['profile_id'] = request.target_profile_id
        
        # Move files
        shutil.move(pending_video, approved_video)
        
        # Save updated metadata
        with open(approved_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Remove old metadata if exists
        if os.path.exists(pending_metadata):
            os.remove(pending_metadata)
        
        # Execution is now handled by the Queue Worker (core/queue_worker.py)
        # which monitors the 'approved' directory and processes sequentially.
        
        # [SYN-FIX] Ensure Scheduler knows the file moved!
        # When we move pending -> approved, any scheduled items in DB pointing to pending path must be updated.
        from core.scheduler import scheduler_service
        scheduler_service.update_video_path(pending_video, approved_video)
        
        pass
        
        # Notify clients
        current_queue = await get_pending_videos()
        await websocket.notify_queue_update([v.dict() for v in current_queue])

        return {
            "success": True,
            "message": f"Video approved for {request.action} processing",
            "filename": video_filename,
            "action": request.action,
            "schedule_time": request.schedule_time,
            "privacy_level": request.privacy_level,
            "executing": False,
            "queued": True
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
        # [SECURITY] Sanitize video_id to prevent path traversal attacks
        safe_video_id = os.path.basename(video_id)
        if safe_video_id != video_id:
            raise HTTPException(status_code=400, detail="Invalid video_id")
        
        # Find and delete video file
        deleted = False
        for filename in os.listdir(PENDING_DIR):
            if filename.startswith(safe_video_id):
                file_path = os.path.join(PENDING_DIR, filename)
                os.remove(file_path)
                deleted = True
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        
        # Notify clients
        current_queue = await get_pending_videos()
        await websocket.notify_queue_update([v.dict() for v in current_queue])

        return {
            "success": True,
            "message": f"Video {video_id} rejected and removed"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting video: {str(e)}")
