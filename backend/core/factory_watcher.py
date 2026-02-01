import asyncio
import os
import sys
import shutil
import logging
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Set

# Ajuste de path e imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.uploader_monitored import upload_video_monitored
from core import brain
from core.status_manager import status_manager
from core.oracle.visual_cortex import visual_cortex

# Configuração de Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Diretórios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUTS_DIR = os.path.join(BASE_DIR, "inputs")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
DONE_DIR = os.path.join(BASE_DIR, "done")
ERRORS_DIR = os.path.join(BASE_DIR, "errors")
PENDING_DIR = os.path.join(BASE_DIR, "data", "pending")

for d in [INPUTS_DIR, PROCESSING_DIR, DONE_DIR, ERRORS_DIR]: 
    os.makedirs(d, exist_ok=True)

class QueueHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.queue = queue
        self.loop = loop
        self.processed: Set[str] = set()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".mp4"):
            self.trigger(event.src_path)

    def trigger(self, path: str):
        fname = os.path.basename(path)
        
        # 1. Hot Folder Activation: Move to Pending for Approval
        logger.info(f"📂 Hot Folder detectou: {fname}")
        
        # Schedule processing
        if self.loop.is_running():
             self.loop.call_soon_threadsafe(self.queue.put_nowait, path)
        else:
             logger.warning("Event loop not running, skipping hot folder trigger.")

async def wait_for_file_stabilization(path: str, timeout: int = 60) -> bool:
    """Aguarda o arquivo parar de crescer (upload completo) e verifica se não está bloqueado"""
    last_size = -1
    stable_count = 0
    
    for _ in range(timeout):
        if not os.path.exists(path):
            return False
            
        try:
            current_size = os.path.getsize(path)
        except OSError:
            # Arquivo pode estar bloqueado ou sendo movido
            await asyncio.sleep(1)
            continue
            
        if current_size == last_size and current_size > 0:
            stable_count += 1
            if stable_count >= 3: # Estável por 3 segundos
                return True
        else:
            stable_count = 0
            
        last_size = current_size
        await asyncio.sleep(1)
        
    return False

async def worker(queue: asyncio.Queue):
    """Consumidor da Fila: Move de inputs -> pending"""
    logger.info("👷 Worker iniciado (Monitoring Inputs -> Pending)...")
    
    # Ensure pending exists
    os.makedirs(PENDING_DIR, exist_ok=True)

    while True:
        try:
            # Pega tarefa
            original_path = await queue.get()
            fname = os.path.basename(original_path)
            
            # 1. Estabilização
            status_manager.update_bot_status("factory", "busy", f"Stabilizing {fname}...")
            if not await wait_for_file_stabilization(original_path):
                logger.error(f"❌ Arquivo instável ou removido: {fname}")
                queue.task_done()
                status_manager.update_bot_status("factory", "idle", "Waiting...")
                continue
                
            # 2. Mover para PENDING (Queue)
            status_manager.update_bot_status("factory", "busy", f"Queuing {fname}")
            dest_path = os.path.join(PENDING_DIR, fname)
            
            if os.path.exists(dest_path):
                # Rename if collision
                name, ext = os.path.splitext(fname)
                import uuid
                dest_path = os.path.join(PENDING_DIR, f"{name}_{str(uuid.uuid4())[:4]}{ext}")
            
            shutil.move(original_path, dest_path)
            logger.info(f"✅ Arquivo movido para PENDING: {fname}")
            
            # 3. Create Metadata for Queue UI
            import time
            json_path = dest_path + ".json"
            meta = {
                "original_filename": fname,
                "profile_id": "unknown", # Hot folder doesn't know profile
                "uploaded_at": str(time.time()),
                "source": "hot_folder",
                "status": "pending"
            }
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
            
            queue.task_done()
            status_manager.update_bot_status("factory", "idle", "Watching inputs...")

        except Exception as e:
            logger.error(f"💥 Erro processando input: {e}")
            queue.task_done()


async def start_watcher():
    """Starts the watcher and worker in the background (for FastAPI integration)"""
    logger.info("👁️ STARTING FACTORY WATCHER (Background Mode)")
    
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()
    
    # Init Watcher
    handler = QueueHandler(queue, loop)
    observer = Observer()
    observer.schedule(handler, INPUTS_DIR)
    observer.start()
    
    # Scan Initial
    count = 0
    for f in os.listdir(INPUTS_DIR):
        if f.endswith(".mp4"):
            if f.startswith('@') or 'test' in f.lower(): continue
            path = os.path.join(INPUTS_DIR, f)
            handler.trigger(path)
            count += 1
    
    logger.info(f"📥 Factory initialized with {count} files pending.")
    
    # Start Worker Task
    asyncio.create_task(worker(queue))
    
    return observer

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Standalone run wrapper
        async def standalone_main():
            observer = await start_watcher()
            try:
                while True: await asyncio.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                observer.join()

        asyncio.run(standalone_main())
    except KeyboardInterrupt:
        pass
