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

# Configuração de Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Diretórios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPROVED_DIR = os.path.join(BASE_DIR, "data", "approved")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
DONE_DIR = os.path.join(BASE_DIR, "done")
ERRORS_DIR = os.path.join(BASE_DIR, "errors")

for d in [APPROVED_DIR, PROCESSING_DIR, DONE_DIR, ERRORS_DIR]:
    os.makedirs(d, exist_ok=True)


async def execute_approved_video(video_filename: str) -> dict:
    """
    Execute upload for a single approved video.
    
    Args:
        video_filename: Filename in approved/ directory
        
    Returns:
        dict with status and message
    """
    logger.info(f"🚀 Iniciando execução manual: {video_filename}")
    
    approved_path = os.path.join(APPROVED_DIR, video_filename)
    
    if not os.path.exists(approved_path):
        return {"status": "error", "message": f"Video {video_filename} not found in approved/"}
    
    # Load metadata
    metadata_path = os.path.join(APPROVED_DIR, f"{video_filename}.json")
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    
    # Extract profile from metadata or filename
    profile_id = metadata.get('profile_id', 'p1')
    
    # Convert short profile ID to full session name
    # Convert short profile ID to full session name
    if profile_id.startswith('p') and not profile_id.startswith('ptiktok'):
        profile_number = profile_id[1:]
        session_name = f"tiktok_profile_{profile_number.zfill(2)}"
    elif profile_id.startswith('ptiktok'):
         # Fix for edge case where "ptiktok_profile_01" was used
         session_name = profile_id[1:]
    else:
        session_name = profile_id
    
    # Move to processing
    status_manager.update_status("busy", video_filename, 10, "Movendo para Processing...", logs=["Movendo arquivo..."])
    proc_path = os.path.join(PROCESSING_DIR, video_filename)
    try:
        if os.path.exists(proc_path):
            os.remove(proc_path)
        shutil.move(approved_path, proc_path)
    except Exception as e:
        logger.error(f"❌ Erro ao mover para processing: {e}")
        status_manager.update_status("error", logs=[f"Erro de I/O: {e}"])
        return {"status": "error", "message": str(e)}
    
    # Get caption (use from metadata or generate with Brain)
    caption = metadata.get('caption')
    if not caption:
        status_manager.update_status("busy", video_filename, 20, "Gerando Legenda (Brain AI)...", logs=["Analisando vídeo com IA..."])
        logger.info("🧠 Brain gerando caption...")
        brain_data = await brain.generate_smart_caption(video_filename)
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

    status_manager.update_status("busy", video_filename, 40, "Iniciando Upload Automático", logs=["Abrindo navegador...", f"Perfil: {session_name}", f"Privacidade: {privacy_level}"])

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
        if result["status"] == "ready":
             # Success handled by queue worker mostly, but we can update logs
             pass
        else:
             pass
             
        return result # Return result to queue worker to finalized status
            
    except Exception as e:
        logger.error(f"💥 Erro fatal: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


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
