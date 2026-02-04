
import sys
import os
import time
import asyncio
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QueueWorker")

# Caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPROVED_DIR = os.path.join(BASE_DIR, "data", "approved")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing") # Where zombies live
DONE_DIR = os.path.join(BASE_DIR, "data", "done")

# Adicionar root ao path para imports
sys.path.append(BASE_DIR)

from core.manual_executor import execute_approved_video
from core.status_manager import status_manager

import shutil

def cleanup_done_files():
    """
    Deletes files in done/ that are older than 48 hours to prevent disk bloat.
    """
    if not os.path.exists(DONE_DIR):
        return
        
    logger.info("🧹 Executing Disk Cleanup (Done Folder)...")
    cleaned_count = 0
    now = time.time()
    cutoff = now - (48 * 3600) # 48 hours
    
    for filename in os.listdir(DONE_DIR):
        file_path = os.path.join(DONE_DIR, filename)
        try:
            if os.path.getmtime(file_path) < cutoff:
                os.remove(file_path)
                logger.info(f"🗑️ Cleaned old file: {filename}")
                cleaned_count += 1
        except Exception as e:
            logger.error(f"Error cleaning {filename}: {e}")
            
    if cleaned_count > 0:
        logger.info(f"✨ Cleanup removed {cleaned_count} old files.")

def recover_zombie_tasks():
    """
    Checks for files stuck in processing/ (zombies) and moves them back to approved/.
    This happens if the server crashed during execution.
    """
    if not os.path.exists(PROCESSING_DIR):
        return

    logger.info("🧟 Verificando tarefas zumbis (falhas anteriores)...")
    moved_count = 0
    
    for filename in os.listdir(PROCESSING_DIR):
        if filename.endswith(".mp4"):
            src = os.path.join(PROCESSING_DIR, filename)
            
            # [SYN-FIX] Idempotency Check
            # Check if this file was actually completed but process crashed before move
            marker = src + ".completed"
            if os.path.exists(marker):
                logger.info(f"✅ Recovering COMPLETED Zombie directly to DONE: {filename}")
                dst = os.path.join(DONE_DIR, filename)
                try:
                    if os.path.exists(dst): os.remove(dst)
                    shutil.move(src, dst)
                    
                    # Move sidecar json
                    meta_src = src + ".json"
                    meta_dst = os.path.join(DONE_DIR, filename + ".json")
                    if os.path.exists(meta_src):
                        if os.path.exists(meta_dst): os.remove(meta_dst)
                        shutil.move(meta_src, meta_dst)
                    
                    # Clean marker
                    os.remove(marker)
                    continue # Skip moving to approved
                except Exception as e:
                     logger.error(f"❌ Failed to move completed zombie to done: {e}")
            
            # Default: Move back to approved (Retry)
            dst = os.path.join(APPROVED_DIR, filename)
            
            try:
                # If destination exists, we might overwrite or rename. 
                # Rename ensures we don't lose the new one if coincidentally same name (unlikely with timestamps).
                # But overwrite is cleaner for retries.
                if os.path.exists(dst):
                    logger.warning(f"⚠️ Zombie {filename} conflita com arquivo em approved. Sobrescrevendo.")
                    os.remove(dst)
                
                shutil.move(src, dst)
                logger.info(f"❤️ Ressuscitando Zombie: {filename} -> approved/")
                moved_count += 1
                
                # Also move metadata json if exists
                meta_json = filename + ".json"
                src_meta = os.path.join(PROCESSING_DIR, meta_json)
                dst_meta = os.path.join(APPROVED_DIR, meta_json)
                if os.path.exists(src_meta):
                    if os.path.exists(dst_meta): os.remove(dst_meta)
                    shutil.move(src_meta, dst_meta)
                    
            except Exception as e:
                logger.error(f"❌ Falha ao recuperar zombie {filename}: {e}")

    if moved_count > 0:
        logger.info(f"✅ {moved_count} tarefas zumbis recuperadas e enfileiradas novamente.")

async def worker_loop():
    logger.info("🚀 Queue Worker Iniciado - Monitorando pasta APPROVED...")
    logger.info(f"📂 Diretório: {APPROVED_DIR}")
    
    # Run Validations/Cleanups
    recover_zombie_tasks()
    cleanup_done_files()
    
    while True:
        try:
            # Lista arquivos
            if not os.path.exists(APPROVED_DIR):
                os.makedirs(APPROVED_DIR)
                
            files = [f for f in os.listdir(APPROVED_DIR) if f.endswith('.mp4')]
            
            if not files:
                # Fila vazia
                await asyncio.sleep(5)
                continue
                
            # Ordenar por data de modificação (FIFO - First In First Out)
            # Queremos o mais antigo primeiro
            files_with_time = []
            for f in files:
                full_path = os.path.join(APPROVED_DIR, f)
                mtime = os.path.getmtime(full_path)
                files_with_time.append((f, mtime))
            
            # Sort by timestamp ascending (oldest first)
            files_with_time.sort(key=lambda x: x[1])
            
            # Select first
            target_file = files_with_time[0][0]
            logger.info(f"⚡ Processando item da fila: {target_file}")
            
            # Execute (Síncrono para o worker, espera terminar)
            start_time = time.time()
            try:
                # Report Start
                status_manager.update_status(
                    state="busy",
                    current_task=target_file,
                    step="Iniciando processamento...",
                    progress=5,
                    logs=[f"Encontrado: {target_file}"]
                )

                result = await execute_approved_video(target_file)
                duration = time.time() - start_time
                
                status = result.get('status', 'unknown')
                logger.info(f"✅ Concluído: {target_file} | Status: {status} | Tempo: {duration:.1f}s")
                
                # Report Done
                if status == 'success':
                    status_manager.update_status("idle", progress=100, step="Concluído com sucesso", logs=[f"Finalizado em {duration:.1f}s"])
                else:
                    status_manager.update_status("error", step="Falha no processamento", logs=[result.get('message', 'Erro desconhecido')])
                    time.sleep(5) # Pause to let user see error status before idle
                    status_manager.set_idle()
                
            except Exception as e:
                logger.error(f"❌ Falha ao processar {target_file}: {e}")
                import traceback
                traceback.print_exc()
                
                # IMPORTANT: Se falhar e não mover o arquivo, vai entrar em loop infinito tentando o mesmo arquivo.
                # O execute_approved_video já deve mover para errors/ ou done/.
                # Se ainda estiver em approved, precisamos mover para errors forçadamente.
                if os.path.exists(os.path.join(APPROVED_DIR, target_file)):
                     logger.warning(f"⚠️ Arquivo preso em approved após erro: {target_file}. Movendo para ERROR_FORCE.")
                     # ... (implementar movimento forçado se necessário, mas manual_executor já tem try/except global que move para errors)
            
            # Pequena pausa entre jobs para o sistema respirar
            await asyncio.sleep(2)
            
        except KeyboardInterrupt:
            logger.info("🛑 Worker interrompido pelo usuário.")
            break
        except asyncio.CancelledError:
            logger.info("🛑 Worker cancelado pelo sistema (Shutdown).")
            # Cleanup if needed
            break
        except Exception as global_e:
            logger.error(f"💥 Erro crítico no worker loop: {global_e}")
            await asyncio.sleep(10) # Wait before restart loop

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        pass
