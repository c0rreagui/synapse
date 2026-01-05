"""
Factory Watcher - Synapse Ingestion Engine
Monitors the inputs folder for new videos and processes them through the upload pipeline.
"""
import asyncio
import os
import sys
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent dir to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uploader import upload_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'factory.log'))
    ]
)
logger = logging.getLogger(__name__)

# Folder paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUTS_DIR = os.path.join(BASE_DIR, "inputs")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
DONE_DIR = os.path.join(BASE_DIR, "done")
ERRORS_DIR = os.path.join(BASE_DIR, "errors")

# ========== MULTI-TENANCY PROFILE MAP ==========
# Maps filename tags to session files
# Usage: @p1_video.mp4 -> uses tiktok_profile_01.json
#        @p2_funny.mp4 -> uses tiktok_profile_02.json
#        video.mp4     -> uses default (tiktok_profile_01.json)
PROFILE_MAP = {
    "@p1": "tiktok_profile_01",
    "@p2": "tiktok_profile_02",
    "@p3": "tiktok_profile_03",
    "@main": "tiktok_profile_01",
    "@backup": "tiktok_profile_02",
}

DEFAULT_PROFILE = "tiktok_profile_01"

def parse_profile_from_filename(filename: str) -> tuple:
    """
    Parse profile tag from filename.
    
    Args:
        filename: e.g., "@p2_funny_video.mp4"
        
    Returns:
        tuple: (session_name, clean_filename)
        - session_name: The session to use (e.g., "tiktok_profile_02")
        - clean_filename: Filename without profile tag (e.g., "funny_video.mp4")
    """
    base = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    
    for tag, session in PROFILE_MAP.items():
        if base.startswith(tag + "_"):
            # Found a tag - extract clean name
            clean_base = base[len(tag) + 1:]  # Remove tag and underscore
            clean_filename = clean_base + ext
            return session, clean_filename
        elif base == tag:
            # Filename is just the tag (unlikely but handle it)
            return session, filename
    
    # No tag found - use default
    return DEFAULT_PROFILE, filename

# ================================================

# Ensure all directories exist
for d in [INPUTS_DIR, PROCESSING_DIR, DONE_DIR, ERRORS_DIR]:
    os.makedirs(d, exist_ok=True)


class VideoHandler(FileSystemEventHandler):
    """Handles file creation events in the inputs folder."""
    
    def __init__(self, loop):
        self.loop = loop
        self.processing_queue = set()  # Track files being processed
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # Only process MP4 files
        if not filename.lower().endswith('.mp4'):
            logger.info(f"Ignoring non-mp4 file: {filename}")
            return
            
        # Avoid duplicate processing
        if filepath in self.processing_queue:
            return
            
        logger.info(f"🎬 New video detected: {filename}")
        self.processing_queue.add(filepath)
        
        # Schedule processing in the async loop
        asyncio.run_coroutine_threadsafe(
            self.process_video(filepath),
            self.loop
        )
    
    async def process_video(self, filepath: str):
        """Process a video through the upload pipeline."""
        filename = os.path.basename(filepath)
        
        try:
            # ========== MULTI-TENANCY ROUTING ==========
            session_name, clean_filename = parse_profile_from_filename(filename)
            
            # Log the routing decision
            if filename != clean_filename:
                logger.info(f"🔀 ROUTING: {filename} -> Perfil: {session_name}")
                print(f"\n{'='*50}")
                print(f"🔀 Arquivo detectado: {filename}")
                print(f"   -> Roteando para: {session_name}")
                print(f"   -> Nome limpo: {clean_filename}")
                print(f"{'='*50}\n")
            else:
                logger.info(f"📌 DEFAULT ROUTE: {filename} -> Perfil: {session_name}")
                print(f"\n📌 Arquivo: {filename} -> Usando perfil padrão: {session_name}\n")
            # =============================================
            
            # Wait for file to stabilize (avoid processing incomplete transfers)
            logger.info(f"⏳ Waiting for file to stabilize: {filename}")
            if not await self.wait_for_stable_file(filepath):
                logger.error(f"File did not stabilize: {filename}")
                self.processing_queue.discard(filepath)
                return
            
            # Move to processing folder
            processing_path = os.path.join(PROCESSING_DIR, filename)
            logger.info(f"📦 Moving to processing: {filename}")
            shutil.move(filepath, processing_path)
            
            # Check for Metadata JSON (Sidecar)
            # Expecting filename.mp4.json
            metadata_filename = f"{filename}.json"
            metadata_src = os.path.join(INPUTS_DIR, metadata_filename)
            metadata_proc = os.path.join(PROCESSING_DIR, metadata_filename)
            
            video_caption = f"{os.path.splitext(clean_filename)[0]} - Synapse Auto"
            schedule_time = None
            
            if os.path.exists(metadata_src):
                logger.info(f"📄 Found metadata sidecar: {metadata_filename}")
                shutil.move(metadata_src, metadata_proc)
                
                try:
                    import json
                    with open(metadata_proc, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        if meta.get("caption"):
                            video_caption = meta.get("caption")
                        if meta.get("schedule_time"):
                            schedule_time = meta.get("schedule_time")
                            logger.info(f"⏰ SCHEDULE DETECTED: {schedule_time}")
                except Exception as e:
                    logger.error(f"⚠️ Error reading metadata: {e}")

            # Call the uploader with the routed session
            logger.info(f"🚀 Starting upload: {filename} (Session: {session_name})")
            result = await upload_video(
                session_name=session_name,  # Dynamic session!
                video_path=processing_path,
                caption=video_caption,
                schedule_time=schedule_time, # Pass scheduling info
                hashtags=["fy", "viral", "synapse"],
                post=False  # Safety: don't auto-post
            )
            
            # Check result and move accordingly
            if result.get("status") in ["ready", "posted"]:
                # Success - move to done
                done_path = os.path.join(DONE_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
                shutil.move(processing_path, done_path)
                
                # Move metadata if exists
                if os.path.exists(metadata_proc):
                    shutil.move(metadata_proc, done_path + ".json")
                    
                logger.info(f"✅ SUCCESS: {filename} -> done/")
                logger.info(f"   Screenshot: {result.get('screenshot_path')}")
            else:
                # Error - move to errors
                error_path = os.path.join(ERRORS_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
                shutil.move(processing_path, error_path)
                
                # Move metadata if exists
                if os.path.exists(metadata_proc):
                    shutil.move(metadata_proc, error_path + ".json")
                    
                logger.error(f"❌ FAILED: {filename} -> errors/")
                logger.error(f"   Reason: {result.get('message')}")
                
                # Write error log
                error_log_path = error_path + ".error.txt"
                with open(error_log_path, 'w') as f:
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"File: {filename}\n")
                    f.write(f"Error: {result.get('message')}\n")
                    
        except Exception as e:
            logger.error(f"💥 Exception processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to move to errors if file still exists
            try:
                if os.path.exists(filepath):
                    error_path = os.path.join(ERRORS_DIR, f"exception_{filename}")
                    shutil.move(filepath, error_path)
            except:
                pass
                
        finally:
            self.processing_queue.discard(filepath)
    
    async def wait_for_stable_file(self, filepath: str, timeout: int = 30, check_interval: float = 1.0) -> bool:
        """Wait for file size to stabilize (indicates transfer complete)."""
        if not os.path.exists(filepath):
            return False
            
        last_size = -1
        stable_count = 0
        elapsed = 0
        
        while elapsed < timeout:
            if not os.path.exists(filepath):
                return False
                
            current_size = os.path.getsize(filepath)
            
            if current_size == last_size and current_size > 0:
                stable_count += 1
                if stable_count >= 3:  # Stable for 3 checks (3 seconds)
                    logger.info(f"   File stable at {current_size / (1024*1024):.2f} MB")
                    return True
            else:
                stable_count = 0
                
            last_size = current_size
            await asyncio.sleep(check_interval)
            elapsed += check_interval
            
        return False


async def main():
    """Main entry point for the factory watcher."""
    print("=" * 60)
    print("🏭 SYNAPSE FACTORY WATCHER - MULTI-TENANCY MODE")
    print("=" * 60)
    print(f"📂 Watching: {INPUTS_DIR}")
    print(f"📦 Processing: {PROCESSING_DIR}")
    print(f"✅ Done: {DONE_DIR}")
    print(f"❌ Errors: {ERRORS_DIR}")
    print("-" * 60)
    print("🔑 Profile Map:")
    for tag, session in PROFILE_MAP.items():
        print(f"   {tag}_ -> {session}")
    print(f"   (default) -> {DEFAULT_PROFILE}")
    print("=" * 60)
    print("⏳ Waiting for videos... (Drop .mp4 files into 'inputs' folder)")
    print("   Example: @p2_funny_video.mp4 -> uses profile 02")
    print("   Press Ctrl+C to stop\n")
    
    # Get the current event loop
    loop = asyncio.get_event_loop()
    
    # Create handler and observer
    handler = VideoHandler(loop)
    observer = Observer()
    observer.schedule(handler, INPUTS_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down factory watcher...")
        observer.stop()
        
    observer.join()
    print("👋 Factory watcher stopped.")


if __name__ == "__main__":
    asyncio.run(main())
