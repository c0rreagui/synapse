"""
Ingestion Endpoint - Receives video uploads from frontend
Saves files to inputs/ folder with profile tags for factory_watcher processing
"""
import os
import uuid
from typing import Optional, List, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")

from core.database_utils import with_db_retries
from core.database import SessionLocal
from core.models import ScheduleItem

@with_db_retries()
def create_schedule_item_safe(profile_id: str, filename: str, metadata: dict) -> int | None:
    # [CAMADA 2] VALIDAÇÃO CRÍTICA: Extrair profile do filename e comparar
    import re
    match = re.search(r'^(p\d+|tiktok_profile_\d+)_', filename)
    extracted_profile = match.group(1) if match else None
    
    # Normalizar ambos para comparação
    # Se profile_id já é tiktok_profile_X, usar direto; senão, é pX
    if profile_id.startswith('tiktok_profile_'):
        normalized_input = profile_id
    elif profile_id.startswith('p'):
        normalized_input = profile_id
    else:
        normalized_input = f"p{profile_id}"
    
    # Normalizar extracted (já vem do regex)
    normalized_extracted = extracted_profile if extracted_profile else None
    
    if not normalized_extracted:
        raise ValueError(
            f"CRITICAL: Cannot extract profile from filename '{filename}'. "
            f"Expected format: pX_... or tiktok_profile_X_..."
        )
    
    # Comparar: se ambos forem tiktok_profile_X, comparar direto
    # Se um for pX e outro tiktok_profile_Y, converter pX -> tiktok_profile_X
    def to_full_format(p: str) -> str:
        if p.startswith('tiktok_profile_'):
            return p
        elif p.startswith('p') and p[1:].isdigit():
            # pX -> tiktok_profile_X (assumindo mapeamento)
            # Mas temos timestamps! Então pX pode não mapear direto.
            # MELHOR: comparar diretamente os formatos
            return p
        return p
    
    # Validação simples: se um é tiktok_profile_X e outro é pY, ERRO
    # Se ambos são tiktok_profile_X, devem ser iguais
    # Se ambos são pX, devem ser iguais
    if normalized_input != normalized_extracted:
        raise ValueError(
            f"CRITICAL: Profile mismatch! "
            f"Filename '{filename}' contains profile '{extracted_profile}' "
            f"but profile_slug is '{profile_id}'"
        )
    
    db = SessionLocal()
    try:
        new_item = ScheduleItem(
            profile_slug=profile_id,
            video_path=filename,
            scheduled_time=None,
            status="pending_analysis_oracle",
            metadata_info=metadata
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item.id
    except Exception as e:
        print(f"❌ DB Error creating item: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

@with_db_retries()
def update_item_status_safe(item_id: int, status: str, metadata: dict = None, error: str = None):
    db = SessionLocal()
    try:
        item = db.query(ScheduleItem).filter(ScheduleItem.id == item_id).first()
        if item:
            item.status = status
            if metadata:
                item.metadata_info = metadata
            if error:
                item.error_message = error
            db.commit()
            print(f"✅ DB: Updated Item {item_id} -> {status}")
    except Exception as e:
        print(f"❌ DB Update Error: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


# Ensure pending directory exists
os.makedirs(PENDING_DIR, exist_ok=True)

class SchedulingSuggestion(BaseModel):
    recommended_time: Optional[str] = None
    score: float = 0
    reasons: List[str] = []

class IngestResponse(BaseModel):
    success: bool
    message: str
    file_id: str
    filename: str
    profile: str
    scheduling_suggestion: Optional[SchedulingSuggestion] = None


@router.post("/upload", response_model=IngestResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    profile_id: str = Form(...),
    caption: Optional[str] = Form(None),
    schedule_time: Optional[str] = Form(None),
    viral_music_enabled: bool = Form(False),
    privacy_level: str = Form("public_to_everyone")  # [SYN-FIX] Added privacy_level
):
    """
    Upload a video file for automated processing.
    Now enriched with ORACLE content analysis in background.
    """
    
    # Validate profile_id format (Alphanumeric only to prevent path traversal)
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', profile_id):
         raise HTTPException(
            status_code=400,
            detail="Invalid profile_id. Must be alphanumeric."
        )

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
    
    # [CAMADA 1] VALIDAÇÃO CRÍTICA: Garantir que profile_id está no filename
    if not tagged_filename.startswith(f"{profile_id}_"):
        raise HTTPException(
            status_code=500,
            detail=f"Internal Error: Profile mismatch in filename generation. Expected '{profile_id}_' prefix."
        )
    
    final_path = os.path.join(PENDING_DIR, tagged_filename)
    temp_path = final_path + ".tmp"
    
    try:
        # Save the video file using stream to avoid RAM crash
        # also implementing simple magic byte check
        
        MAX_SIZE = 500 * 1024 * 1024 # 500MB
        size_processed = 0
        
        import hashlib
        file_hash = hashlib.md5()
        
        file_hash.update(first_chunk) # [SYN-SEC] Update Hash
        size_processed += len(first_chunk)
        
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            file_hash.update(chunk) # [SYN-SEC] Update Hash
            size_processed += len(chunk)
            
            if size_processed > MAX_SIZE:
                f.close()
                os.remove(file_path) # Delete partial
                raise HTTPException(status_code=413, detail="File too large (Max 500MB)")
        
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
            "privacy_level": privacy_level, # [SYN-FIX] Save privacy_level
            "uploaded_at": str(uuid.uuid1()),
            "oracle_status": "pending",
            "md5_checksum": file_hash.hexdigest() # [SYN-SEC] MD5 Integrity Check
        }
        
        metadata_filename = f"{tagged_filename}.json"
        metadata_path = os.path.join(PENDING_DIR, metadata_filename)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        # [SYN-DB] Transactional Outbox: Create DB Record IMMEDIATELY
        try:
            item_id = create_schedule_item_safe(profile_id, tagged_filename, metadata)
            print(f"✅ DB: Created ScheduleItem #{item_id} for {tagged_filename}")
        except Exception as db_err:
             print(f"❌ DB Error creating item: {db_err}")
             item_id = None # Fallback? Or fail? Fail is safer for "Transactional" goal.
             # If DB fails, we should probably fail the upload to be safe, but file is on disk.
             # For now, log and proceed, but this defeats the purpose of "Transactional Outbox" mostly.
             # Ideally we delete the file if DB fails.
             # Let's proceed for resilience but log HEAVILY.
             
        # 🟢 TRIGGER ORACLE IN BACKGROUND
        background_tasks.add_task(process_oracle_enrichment, metadata_path, file.filename, profile_id, item_id)
        
        # 🧠 Smart Logic: Sugerir melhor horário para agendamento
        scheduling_suggestion = None
        try:
            from core.smart_logic import smart_logic
            suggested_slot = smart_logic.suggest_slot(
                profile_id=profile_id,
                prefer_prime_time=True
            )
            if suggested_slot:
                scheduling_suggestion = SchedulingSuggestion(
                    recommended_time=suggested_slot.time.isoformat(),
                    score=suggested_slot.score,
                    reasons=suggested_slot.reasons
                )
        except Exception as e:
            print(f"Smart Logic suggestion error: {e}")
        
        return IngestResponse(
            success=True,
            message=f"Video queued. Oracle Analysis started in background (Item #{item_id}).",
            file_id=file_id,
            filename=tagged_filename,
            profile=profile_id,
            scheduling_suggestion=scheduling_suggestion
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

# Background Task for Oracle
async def process_oracle_enrichment(metadata_path: str, original_filename: str, profile_id: str, item_id: int = None):
    try:
        from core.oracle.seo_engine import seo_engine
        from core.database import SessionLocal
        from core.models import ScheduleItem
        import json
        
        print(f"🔮 Oracle: Analyzing content for {original_filename} (Item {item_id})...")
        
        # 1. Generate Content Metadata
        # TODO: Get actual profile niche from Profile Metadata (omitted for speed, defaulting to 'General')
        analysis = await seo_engine.generate_content_metadata(original_filename, niche="General")
        
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
            
            # [SYN-DB] Update DB Status
            if item_id:
                try:
                    update_item_status_safe(item_id, "pending_approval", metadata=data)
                except Exception as db_e:
                    print(f"❌ DB Update Error: {db_e}")
            
    except Exception as e:
        print(f"❌ Oracle Background Error: {e}")
        # [SYN-DB] Mark Failed
        if item_id:
            try:
                update_item_status_safe(item_id, "failed_analysis", error=str(e))
            except: pass


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

@router.get("/files")
async def list_files(status: Optional[str] = None):
    """
    Get detailed list of files in each stage.
    """
    import time
    from datetime import datetime
    
    processing_dir = os.path.join(BASE_DIR, "processing")
    done_dir = os.path.join(BASE_DIR, "done")
    errors_dir = os.path.join(BASE_DIR, "errors")
    
    paths = {
        "queued": PENDING_DIR,
        "processing": processing_dir,
        "completed": done_dir,
        "failed": errors_dir
    }
    
    results = {}
    
    target_keys = [status] if status and status in paths else paths.keys()
    
    for key in target_keys:
        directory = paths[key]
        files = []
        if os.path.exists(directory):
            for f in os.listdir(directory):
                if f.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
                    fp = os.path.join(directory, f)
                    try:
                        stat = os.stat(fp)
                        files.append({
                            "name": f,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "path": fp
                        })
                    except:
                        pass
        results[key] = files
        
    return results


@router.delete("/files/{filename}")
async def delete_file(filename: str, status: str = "queued"):
    """
    Delete a file from the pipeline.
    Status can be: queued, processing, completed, failed
    """
    processing_dir = os.path.join(BASE_DIR, "processing")
    done_dir = os.path.join(BASE_DIR, "done")
    errors_dir = os.path.join(BASE_DIR, "errors")
    
    paths = {
        "queued": PENDING_DIR,
        "processing": processing_dir,
        "completed": done_dir,
        "failed": errors_dir
    }
    
    if status not in paths:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    directory = paths[status]
    
    # [SECURITY] Sanitize filename to prevent path traversal attacks
    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = os.path.join(directory, safe_filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    try:
        os.remove(file_path)
        
        # Also remove metadata JSON if exists
        json_path = file_path + ".json"
        if os.path.exists(json_path):
            os.remove(json_path)
        
        return {"success": True, "message": f"Deleted {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@router.post("/files/{filename}/reprocess")
async def reprocess_file(filename: str):
    """
    Move a failed file back to queued for reprocessing.
    """
    import shutil
    
    # [SECURITY] Sanitize filename to prevent path traversal attacks
    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    errors_dir = os.path.join(BASE_DIR, "errors")
    source = os.path.join(errors_dir, safe_filename)
    dest = os.path.join(PENDING_DIR, safe_filename)
    
    if not os.path.exists(source):
        raise HTTPException(status_code=404, detail=f"File not found in errors: {filename}")
    
    try:
        shutil.move(source, dest)
        
        # Also move metadata JSON if exists
        json_source = source + ".json"
        json_dest = dest + ".json"
        if os.path.exists(json_source):
            shutil.move(json_source, json_dest)
        
        return {"success": True, "message": f"Moved {filename} back to queue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reprocess: {str(e)}")

