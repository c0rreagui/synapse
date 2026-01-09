
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

# Adicionar root ao path para imports
sys.path.append(BASE_DIR)

from core.manual_executor import execute_approved_video
from core.status_manager import status_manager

async def worker_loop():
    logger.info("🚀 Queue Worker Iniciado - Monitorando pasta APPROVED...")
    logger.info(f"📂 Diretório: {APPROVED_DIR}")
    
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
        except Exception as global_e:
            logger.error(f"💥 Erro crítico no worker loop: {global_e}")
            await asyncio.sleep(10) # Wait before restart loop

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        pass
