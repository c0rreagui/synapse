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
        
        # AUTO-PROCESSING DISABLED - Manual approval workflow active
        # Files are now processed via manual approval in /api/v1/queue
        logger.info(f"ℹ️ Arquivo detectado (auto-processing desabilitado): {fname}")
        logger.info(f"   Use o painel de aprovação para processar este arquivo.")
        return
        
        # Original auto-processing code below (disabled)
        # # Ignora testes
        # if fname.startswith('@') or 'test' in fname.lower():
        #     logger.info(f"⏭️ Ignorando arquivo de teste: {fname}")
        #     return
        #     
        # if path not in self.processed:
        #     logger.info(f"📥 Enfileirado: {fname}")
        #     self.processed.add(path)
        #     # Coloca na fila de forma thread-safe
        #     self.loop.call_soon_threadsafe(self.queue.put_nowait, path)

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
    """Consumidor da Fila: Processa um vídeo por vez"""
    logger.info("👷 Worker iniciado e aguardando tarefas...")
    
    while True:
        try:
            # Pega tarefa
            original_path = await queue.get()
            fname = os.path.basename(original_path)
            
            logger.info(f"🎬 Iniciando processamento: {fname}")
            
            # 1. Estabilização
            if not await wait_for_file_stabilization(original_path):
                logger.error(f"❌ Arquivo instável, incompleto ou inacessível: {fname}")
                # Remove do processed set para permitir retentativa futura se recriado
                # (Seria ideal ter acesso ao handler, mas ok por agora)
                queue.task_done()
                continue
                
            # 2. Mover para Processing
            proc_path = os.path.join(PROCESSING_DIR, fname)
            try:
                # Se já existir em processing, remove (limpeza de falha anterior)
                if os.path.exists(proc_path):
                    os.remove(proc_path)
                shutil.move(original_path, proc_path)
                
                # Move Sidecar JSON if exists
                original_json = original_path + ".json"
                proc_json = proc_path + ".json"
                sidecar_data = {}
                
                if os.path.exists(original_json):
                     if os.path.exists(proc_json): os.remove(proc_json)
                     shutil.move(original_json, proc_json)
                     # Load Sidecar Data
                     try:
                         with open(proc_json, 'r', encoding='utf-8') as f:
                             sidecar_data = json.load(f)
                         logger.info(f"📄 Metadados laterais carregados: {sidecar_data}")
                     except Exception as e:
                         logger.error(f"⚠️ Erro ao ler JSON lateral: {e}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao mover para processing: {e}")
                queue.task_done()
                continue
                
            # 3. Brain: Gerar Metadados
            logger.info("🧠 Brain analisando conteúdo...")
            brain_data = await brain.generate_smart_caption(fname)
            
            # Merge com Sidecar (Override)
            final_caption = sidecar_data.get("caption") or brain_data["caption"]
            final_schedule = sidecar_data.get("schedule_time") # None se não houver
            viral_boost = sidecar_data.get("viral_music_enabled", False)

            meta = {
                "caption": final_caption,
                "hashtags": brain_data["hashtags"],
                "schedule_time": final_schedule,
                "viral_music_enabled": viral_boost
            }
            
            # Salva o JSON gerado pelo Brain na pasta processing para debug
            with open(proc_path + ".json", 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            
            # 4. Upload
            logger.info(f"🚀 Iniciando Upload: {fname}")
            logger.info(f"📝 Legenda: {meta['caption']}")
            
            result = await upload_video_monitored(
                session_name="tiktok_profile_01",
                video_path=proc_path,
                caption=meta["caption"],
                hashtags=meta["hashtags"],
                schedule_time=meta.get("schedule_time"),
                post=False, # Rascunho padrão
                viral_music_enabled=meta.get("viral_music_enabled", False)
            )
            
            # 5. Backup e Cleanup
            if result["status"] == "ready":
                final_dest = os.path.join(DONE_DIR, fname)
                if os.path.exists(final_dest): os.remove(final_dest)
                shutil.move(proc_path, final_dest)
                
                # Move JSON também
                if os.path.exists(proc_path + ".json"):
                    shutil.move(proc_path + ".json", os.path.join(DONE_DIR, fname + ".json"))
                    
                logger.info(f"✅ SUCESSO! Vídeo processado e movido para DONE.")
            else:
                error_dest = os.path.join(ERRORS_DIR, fname)
                if os.path.exists(error_dest): os.remove(error_dest)
                shutil.move(proc_path, error_dest)
                
                # Salva log de erro
                with open(error_dest + ".error.txt", "w", encoding='utf-8') as f:
                    f.write(result.get("message", "Unknown error"))
                logger.error(f"❌ FALHA no Upload. Movido para ERRORS. Msg: {result.get('message')}")
            
        except Exception as e:
            logger.error(f"💥 Erro fatal no worker: {e}", exc_info=True)
        finally:
            queue.task_done()
            logger.info("💤 Worker aguardando próxima tarefa...")

async def main():
    print("👁️ SYNAPSE QUEUE MANAGER + BRAIN ATIVO")
    print("=" * 40)
    print(f"📂 Monitorando: {INPUTS_DIR}")
    print(f"🧠 Brain ativado para geração de legendas")
    
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()
    
    # Inicia Watcher
    handler = QueueHandler(queue, loop)
    observer = Observer()
    observer.schedule(handler, INPUTS_DIR)
    observer.start()
    
    # Scan Inicial
    print("🔍 Escaneando arquivos existentes...")
    count = 0
    for f in os.listdir(INPUTS_DIR):
        if f.endswith(".mp4"):
             # Ignora testes
            if f.startswith('@') or 'test' in f.lower():
                continue
            path = os.path.join(INPUTS_DIR, f)
            handler.trigger(path)
            count += 1
            
    print(f"📥 {count} arquivos na fila inicial.")
    
    # Inicia Worker
    # Worker roda indefinidamente até ser cancelado
    workers = [asyncio.create_task(worker(queue))]
    
    try:
        # Aguarda workers (que nunca terminam sozinhos)
        await asyncio.gather(*workers)
    except KeyboardInterrupt:
        logger.info("🛑 Parando sistema...")
        observer.stop()
        for w in workers: w.cancel()
    
    observer.join()

if __name__ == "__main__":
    try:
        # Policy fix para Windows (evita RuntimeError em loop closure)
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
