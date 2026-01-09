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
    if profile_id.startswith('p'):
        profile_number = profile_id[1:]
        session_name = f"tiktok_profile_{profile_number.zfill(2)}"
    else:
        session_name = profile_id
    
    # Move to processing
    proc_path = os.path.join(PROCESSING_DIR, video_filename)
    try:
        if os.path.exists(proc_path):
            os.remove(proc_path)
        shutil.move(approved_path, proc_path)
    except Exception as e:
        logger.error(f"❌ Erro ao mover para processing: {e}")
        return {"status": "error", "message": str(e)}
    
    # Get caption (use from metadata or generate with Brain)
    caption = metadata.get('caption')
    if not caption:
        logger.info("🧠 Brain gerando caption...")
        brain_data = await brain.generate_smart_caption(video_filename)
        caption = brain_data["caption"]
        hashtags = brain_data["hashtags"]
    else:
        hashtags = metadata.get('hashtags', [])
    
    # Get schedule time
    schedule_time = metadata.get('schedule_time')
    action = metadata.get('action', 'immediate')
    
    logger.info(f"📝 Caption: {caption}")
    logger.info(f"📅 Action: {action}")
    if schedule_time:
        logger.info(f"⏰ Schedule: {schedule_time}")
    
    # Execute upload
    try:
        result = await upload_video_monitored(
            session_name=session_name,
            video_path=proc_path,
            caption=caption,
            hashtags=hashtags,
            schedule_time=schedule_time if action == 'scheduled' else None,
            post=(action == 'immediate'),
            enable_monitor=True  # ENABLED for Audit/Debugging
        )
        
        # Move to done/errors based on result
        if result["status"] == "ready":
            final_dest = os.path.join(DONE_DIR, video_filename)
            if os.path.exists(final_dest):
                os.remove(final_dest)
            shutil.move(proc_path, final_dest)
            
            # Move metadata
            if os.path.exists(metadata_path):
                shutil.move(metadata_path, os.path.join(DONE_DIR, f"{video_filename}.json"))
            
            logger.info(f"✅ SUCESSO! Vídeo processado: {video_filename}")
            return {"status": "success", "message": "Video uploaded successfully"}
        else:
            error_dest = os.path.join(ERRORS_DIR, video_filename)
            if os.path.exists(error_dest):
                os.remove(error_dest)
            shutil.move(proc_path, error_dest)
            
            # Save error log
            with open(f"{error_dest}.error.txt", "w", encoding='utf-8') as f:
                f.write(result.get("message", "Unknown error"))
            
            logger.error(f"❌ FALHA: {result.get('message')}")
            return {"status": "error", "message": result.get("message", "Upload failed")}
            
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
        logger.info("ℹ️ Nenhum vídeo aprovado encontrado")
        return
    
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
