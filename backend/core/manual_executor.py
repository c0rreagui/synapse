"""
Manual Executor - Processes approved videos on demand
Triggered by approval action, not automatic file watching
"""
import asyncio
import os
import sys
import shutil
import logging
import json
from typing import Optional

# Ajuste de path e imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.uploader_monitored import upload_video_monitored
from core import brain
from core.status_manager import status_manager
from core.consts import ScheduleStatus

# Configuração de Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Diretórios centralizados
from core.config import APPROVED_DIR, PROCESSING_DIR, DONE_DIR, ERRORS_DIR


async def execute_approved_video(
    video_input: str, 
    is_scheduled: bool = False, 
    metadata: Optional[dict] = None,
    processing_id: Optional[str] = None
) -> dict:
    """
    Execute upload for a single approved video.
    
    Args:
        video_input: Filename (rel to approved/) or Absolute Path.
        is_scheduled: If True, indicates triggered by automated scheduler.
        metadata: Optional dict override (e.g. from Scheduler DB).
        
    Returns:
        dict with status and message
    """
    logger.info(f"Iniciando execucao {'agendada' if is_scheduled else 'manual'}: {os.path.basename(video_input)}")
    
    # 1. Determine Source Path and Filename
    # [SYN-FIX] Handle Windows paths passed from Scheduler DB
    if "\\" in video_input or "/" in video_input:
        # It's likely a path (absolute or relative)
        
        # Simple Normalization:
        # 1. Replace backslashes
        clean_path = video_input.replace("\\", "/")
        
        # 2. Check existence as-is (best effort)
        if os.path.exists(video_input):
            source_path = video_input
            video_filename = os.path.basename(video_input)
        elif os.path.exists(clean_path):
             source_path = clean_path
             video_filename = os.path.basename(clean_path)
        else:
             # [SYN-FIX] Try mapping Windows Path (D:/...) to Docker (/app/...)
             # We assume /app/data maps to D:/.../backend/data
             from core.config import DATA_DIR
             
             # Heuristic: Find 'data' in path
             parts = clean_path.split("/data/")
             if len(parts) > 1:
                 # Reconstruct relative to /app/data/
                 relative = parts[-1]
                 candidate = os.path.join(DATA_DIR, relative)
                 if os.path.exists(candidate):
                     source_path = candidate
                     video_filename = os.path.basename(candidate)
                 else:
                     return {"status": ScheduleStatus.FAILED, "message": f"Source file not found (mapped): {candidate}"}
             else:
                 return {"status": ScheduleStatus.FAILED, "message": f"Source file not found: {video_input}"}

    else:
        # Relative to APPROVED_DIR (Legacy/Queue Worker mode)
        video_filename = video_input
        
        # Security: Prevent Path Traversal (Keep this for pure filenames)
        if ".." in video_filename or "/" in video_filename or "\\" in video_filename:
             logger.critical(f"🛑 ATTEMPTED PATH TRAVERSAL IN EXECUTOR: {video_filename}")
             return {"status": "error", "message": "Invalid filename (Path Traversal Detected)"}
        
        source_path = os.path.join(APPROVED_DIR, video_filename)
        if not os.path.exists(source_path):
            return {"status": ScheduleStatus.FAILED, "message": f"Video {video_filename} not found in approved/"}
    
    # 2. Load Metadata (Priority: Argument > JSON Sidecar)
    # If explicit metadata passed (from Scheduler DB), usage that. 
    # Otherwise try to load from formatted JSON sidecar.
    if not metadata:
        metadata = {}
        # Try finding json adjacent to source
        json_path = source_path + ".json"
        
        # If not found, try removing extension (if legacy naming)
        if not os.path.exists(json_path):
             json_path = os.path.splitext(source_path)[0] + ".json"
             
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sidecar metadata: {e}")

    
    # Extract profile from metadata or filename
    profile_id = metadata.get('profile_id') or metadata.get('profile_slug') or metadata.get('tiktok_profile')
    
    # [SYN-FIX] Fallback: Extract profile_id from filename if not in metadata
    # Filenames follow pattern: ptiktok_profile_TIMESTAMP_HASH.mp4 or N_ptiktok_profile_TIMESTAMP_HASH.mp4
    if not profile_id:
        import re
        match = re.search(r'p?(tiktok_profile_\d+)', video_filename)
        if match:
            profile_id = match.group(1)  # Already clean: tiktok_profile_TIMESTAMP
            logger.info(f"Profile ID extraido do filename: {profile_id}")
        else:
            profile_id = 'p1'  # Legacy fallback
    
    # Convert short profile ID to full session name
    if profile_id.startswith('p') and not profile_id.startswith('ptiktok') and not profile_id.startswith('tiktok_profile_'):
        profile_number = profile_id[1:]
        session_name = f"tiktok_profile_{profile_number.zfill(2)}"
    elif profile_id.startswith('ptiktok'):
         # Fix for edge case where "ptiktok_profile_01" was used
         session_name = profile_id[1:]
    else:
        session_name = profile_id
    
    # 🛡️ SAFETY CHECK: Verify if profile is active in DB
    from core import session_manager
    # We use the session_name (slug) to query status
    
    db_meta = session_manager.get_profile_metadata(session_name)
    if db_meta:
        if db_meta.get("active") is False:
            logger.warning(f"🛑 Execução abortada: Perfil {session_name} está INATIVO/BANIDO.")
            status_manager.update_status("error", logs=[f"Perfil {session_name} inativo. Re-autentique."])
            return {"status": "error", "message": "Profile is inactive (disabled in DB)"}
    
    # [SYN-FIX] Lightweight Pre-flight: Cookie-only check (no browser launch)
    # The real session check happens inside uploader_monitored.py in the actual upload browser.
    # Opening a separate headless browser here caused TikTok rate-limiting / false positives.
    from core.session_manager import get_session_path, check_cookies_validity
    session_file = get_session_path(session_name)
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r', encoding='utf-8') as _f:
                _data = json.load(_f)
                _cookies = _data.get("cookies", []) if isinstance(_data, dict) else _data
            if not check_cookies_validity(_cookies):
                logger.warning(f"Cookies expirados para {session_name}, mas tentando upload mesmo assim.")
        except Exception:
            pass
    else:
        logger.error(f"Arquivo de sessao nao encontrado: {session_file}")
        status_manager.update_status("error", logs=[f"Sessao de {session_name} nao encontrada."])
        return {"status": "error", "message": "Session file not found"}
    
    # 3. Move to processing (Unique Path to avoid Race Conditions)
    status_manager.update_status(
        state="busy", 
        current_task=video_filename, 
        progress=10, 
        step="Preparando ambiente único...", 
        logs=["Movendo arquivo para isolamento..."]
    )
    
    # [SYN-FIX] Use processing_id to isolate concurrent runs for same video
    unique_filename = f"{processing_id}_{video_filename}" if processing_id else video_filename
    proc_path = os.path.join(PROCESSING_DIR, unique_filename)
    
    try:
        # If source and dest are same, don't fail
        if os.path.abspath(source_path) != os.path.abspath(proc_path):
            if os.path.exists(proc_path):
                os.remove(proc_path)
            
            # [SYN-FIX] If scheduled, COPY instead of MOVE to preserve source for other profiles
            if is_scheduled:
                shutil.copy(source_path, proc_path)
                logger.info(f"✅ Copied to UNIQUE processing path: {proc_path}")
            else:
                shutil.move(source_path, proc_path)
                logger.info(f"✅ Moved to UNIQUE processing path: {proc_path}")
        else:
            logger.info("Source is already in processing folder.")
    except Exception as e:
        logger.error(f"Erro no isolamento de arquivo: {e}")
        status_manager.update_status("error", logs=[f"Erro de I/O em processamento: {e}"])
        return {"status": ScheduleStatus.FAILED, "message": str(e)}
    
    # Get caption (use from metadata or generate with Brain)
    caption = metadata.get('caption')
    if not caption:
        status_manager.update_status(
            state="busy", 
            current_task=video_filename, 
            progress=20, 
            step="Gerando Legenda (Brain AI)...", 
            logs=["Analisando video com IA..."]
        )
        logger.info("[BRAIN] Brain gerando caption (com Vision)...")
        
        # [SYN-FIX] Use Original Filename for better context/fallback
        # If unavailable, fall back to video_filename (which might be p1_uuid.mp4)
        target_name = metadata.get('original_filename', video_filename)
        
        brain_data = await brain.generate_smart_caption(
            target_name, 
            profile_prefix=profile_id, 
            video_path=proc_path
        )
        caption = brain_data["caption"]
        hashtags = brain_data["hashtags"]
    else:
        hashtags = metadata.get('hashtags', [])
    
    # ... (Schedule logic)
    
    
    # Get privacy level (default to public if not set)
    privacy_level = metadata.get('privacy_level', 'public_to_everyone')
    
    # Get action
    action = metadata.get('action', 'scheduled')
    schedule_time = metadata.get('schedule_time')

    status_manager.update_status(
        state="busy", 
        current_task=video_filename, 
        progress=40, 
        step="Iniciando Upload Automatico", 
        logs=["Abrindo navegador...", f"Perfil: {session_name}", f"Privacidade: {privacy_level}"]
    )

    # Execute upload
    try:
        result = await upload_video_monitored(
            session_name=session_name,
            video_path=proc_path,
            caption=caption,
            hashtags=hashtags,
            schedule_time=schedule_time if action == 'scheduled' else None,
            post=(action == 'immediate'),
            enable_monitor=True,
            viral_music_enabled=metadata.get('viral_music_enabled', False),
            sound_title=metadata.get('sound_title'),  # 🎵 Música viral selecionada
            privacy_level=privacy_level
        )
        
        # ... logic continues ...
        if result["status"] == ScheduleStatus.READY:
             # Success handled by queue worker mostly, but we can update logs
             
             # [SYN-FIX] Idempotency: Create .completed marker in processing folder
             # This prevents Zombie Recovery from reprocessing successful uploads if moving to done fails or server crashes.
             marker_path = proc_path + ".completed"
             try:
                 with open(marker_path, 'w', encoding='utf-8') as f:
                     f.write("success")
                 logger.info(f"✅ Created idempotency marker: {marker_path}")
                 
                 # [SYN-FIX] Completion Move: Move to DONE to avoid becoming a Zombie
                 dest_path = os.path.join(DONE_DIR, video_filename)
                 # Handle overwrite in done if exists
                 if os.path.exists(dest_path):
                     os.remove(dest_path)
                 shutil.move(proc_path, dest_path)
                 logger.info(f"✅ Moved to DONE: {dest_path}")
                 
                 # Move sidecar JSON if exists
                 proc_json = proc_path + ".json"
                 if not os.path.exists(proc_json): # Try no-ext
                     proc_json = os.path.splitext(proc_path)[0] + ".json"
                     
                 if os.path.exists(proc_json):
                     dest_json = os.path.join(DONE_DIR, os.path.basename(proc_json))
                     if os.path.exists(dest_json): os.remove(dest_json)
                     shutil.move(proc_json, dest_json)
                 
                 # Clean marker after successful move (we don't need it if file is gone from processing)
                 if os.path.exists(marker_path):
                     os.remove(marker_path)
                     
             except Exception as e:
                 logger.warning(f"Failed to finalize/move file {video_filename}: {e}")
        else:
             pass
             
        return result # Return result to queue worker to finalized status
            
    except Exception as e:
        logger.error(f"💥 Erro fatal: {e}", exc_info=True)
        # [SYN-FIX] Move to errors so it doesn't get stuck in Processing
        try:
            if 'proc_path' in locals() and os.path.exists(proc_path):
                error_path = os.path.join(ERRORS_DIR, video_filename)
                if os.path.exists(error_path):
                     os.remove(error_path)
                shutil.move(proc_path, error_path)
                logger.info(f"Moved failed video to errors: {error_path}")
        except Exception as move_err:
            logger.error(f"Failed to move to errors: {move_err}")
            
        return {"status": ScheduleStatus.FAILED, "message": str(e)}


async def process_all_approved():
    """
    Process all videos in approved/ directory.
    Used for batch processing or scheduled runs.
    """
    logger.info("📦 Processando todos os vídeos aprovados...")
    
    if not os.path.exists(APPROVED_DIR):
        logger.info(f"ℹ️ Nenhum vídeo aprovado encontrado. Dir not exists: {APPROVED_DIR}")
        return
    
    logger.info(f"📂 Debug Path: {APPROVED_DIR}")
    logger.info(f"📂 Debug List: {os.listdir(APPROVED_DIR)}")
    
    results = []
    for filename in os.listdir(APPROVED_DIR):
        if not filename.endswith('.mp4'):
            continue
        
        result = await execute_approved_video(filename)
        results.append({"filename": filename, "result": result})
    
    logger.info(f"✅ Processamento completo: {len(results)} vídeos")
    return results


if __name__ == "__main__":
    # For testing: process all approved videos
    asyncio.run(process_all_approved())
