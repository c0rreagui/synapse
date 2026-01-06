"""
Factory Watcher V2 - Synapse Engine
Features:
- Integração com JSON de metadados
- Suporte a Agendamento
- Olho Que Tudo Vê (Monitoramento) 👁️
- Scan inicial de arquivos
"""
import asyncio
import os
import sys
import shutil
import logging
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Fix para emojis no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.uploader_monitored import upload_video_monitored

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUTS_DIR = os.path.join(BASE_DIR, "inputs")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
DONE_DIR = os.path.join(BASE_DIR, "done")
ERRORS_DIR = os.path.join(BASE_DIR, "errors")

for d in [INPUTS_DIR, PROCESSING_DIR, DONE_DIR, ERRORS_DIR]: os.makedirs(d, exist_ok=True)

class VideoHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop
        self.queue = set()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".mp4"):
            self.trigger(event.src_path)
            
    def trigger(self, path):
        if path not in self.queue:
            logger.info(f"🎬 Detectado: {os.path.basename(path)}")
            self.queue.add(path)
            asyncio.run_coroutine_threadsafe(self.process(path), self.loop)

    async def process(self, path):
        fname = os.path.basename(path)
        proc_path = os.path.join(PROCESSING_DIR, fname)
        
        # Busca metadados (JSON)
        # Suporta input.mp4.json e input.json
        json_candidates = [path + ".json", os.path.splitext(path)[0] + ".json"]
        meta = {}
        found_json_path = None
        
        # Espera estabilizar escrita
        await asyncio.sleep(2)
        
        for json_path in json_candidates:
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    found_json_path = json_path
                    logger.info(f"📄 Metadados carregados de {os.path.basename(json_path)}")
                    break
                except Exception as e:
                    logger.error(f"⚠️ Erro ao ler JSON {json_path}: {e}")

        try:
            # Move vídeo para processamento
            shutil.move(path, proc_path)
            
            # Move JSON se existir
            curr_json_path = None
            if found_json_path:
                curr_json_path = os.path.join(PROCESSING_DIR, os.path.basename(found_json_path))
                shutil.move(found_json_path, curr_json_path)

            # Executa Upload Monitorado
            schedule_time = meta.get("schedule_time")
            logger.info(f"🚀 Iniciando processo para: {fname}")
            if schedule_time:
                logger.info(f"📅 Agendamento solicitado para: {schedule_time}")
            
            result = await upload_video_monitored(
                session_name="tiktok_profile_01",
                video_path=proc_path, 
                caption=meta.get("caption", f"Upload {fname}"),
                hashtags=meta.get("hashtags", []),
                schedule_time=schedule_time,
                post=False
            )
            
            # Processa resultado
            if result["status"] == "ready":
                dest = os.path.join(DONE_DIR, fname)
                shutil.move(proc_path, dest)
                if curr_json_path: 
                    shutil.move(curr_json_path, os.path.join(DONE_DIR, os.path.basename(curr_json_path)))
                logger.info(f"✅ SUCESSO! Movido para DONE.")
            else:
                dest = os.path.join(ERRORS_DIR, fname)
                shutil.move(proc_path, dest)
                if curr_json_path:
                    shutil.move(curr_json_path, os.path.join(ERRORS_DIR, os.path.basename(curr_json_path)))
                
                # Salva log de erro
                with open(dest + ".error.txt", "w", encoding='utf-8') as f:
                    f.write(result.get("message", "Unknown error"))
                logger.error(f"❌ FALHA. Movido para ERRORS. Msg: {result.get('message')}")
                
        except Exception as e:
            logger.error(f"💥 Falha crítica no watcher: {e}", exc_info=True)
        finally:
            self.queue.discard(path)

async def main():
    print("👁️ SYNAPSE WATCHER + MONITOR ATIVO")
    print("=" * 40)
    print(f"📂 Monitorando: {INPUTS_DIR}")
    
    loop = asyncio.get_event_loop()
    handler = VideoHandler(loop)
    observer = Observer()
    observer.schedule(handler, INPUTS_DIR)
    observer.start()
    
    # scan inicial
    print("🔍 Escaneando arquivos existentes...")
    for f in os.listdir(INPUTS_DIR):
        if f.endswith(".mp4"):
            path = os.path.join(INPUTS_DIR, f)
            handler.trigger(path)
            
    try:
        while True: await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    asyncio.run(main())
