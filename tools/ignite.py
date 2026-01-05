import subprocess
import time
import os
import sys

def main():
    print("--- 🔌 INICIANDO SYNAPSE (MODO DIRETO + UTF-8) ---")
    
    # Lista para guardar os processos
    processes = []
    
    try:
        # 1. API (Backend)
        # stdout=None faz o log sair direto no terminal, sem passar pelo Python (Zero erro de encoding)
        print(">>> Lançando API...")
        # Adicionando PYTHONPATH para garantir que backend seja encontrado
        # Mas mantendo o comando simples como pedido.
        # Nota: O erro de import 'No module named app' requer fix no código ou PYTHONPATH.
        # Vou injetar PYTHONPATH no ambiente deste subprocesso apenas para garantir.
        # E TAMBÉM forçar UTF-8 para evitar crash de encoding no Windows
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd() + os.pathsep + os.path.join(os.getcwd(), "backend") + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
        
        p_api = subprocess.Popen("uvicorn backend.app.main:app --reload --port 8000", shell=True, env=env)
        processes.append(p_api)
        time.sleep(2) # Dá um tempinho pra API respirar

        # 2. Frontend (Web)
        print(">>> Lançando Frontend...")
        p_web = subprocess.Popen("npm run dev", cwd="frontend", shell=True, env=env)
        processes.append(p_web)

        # 3. Watcher (Robô)
        print(">>> Lançando Robô Watcher...")
        p_bot = subprocess.Popen("python backend/core/factory_watcher.py", shell=True, env=env)
        processes.append(p_bot)

        print("\n✅ TUDO RODANDO! Os logs aparecerão abaixo misturados.")
        print("❌ Pressione Ctrl+C para encerrar tudo.\n")
        
        # Mantém o script vivo para segurar os processos
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 INTERRUPÇÃO DETECTADA! Matando processos...")
        
        # No Windows, matar o pai não mata os filhos. Precisamos ser agressivos.
        # O 'taskkill' vai garantir que não sobre nada rodando escondido.
        os.system("taskkill /F /IM uvicorn.exe /T >nul 2>&1")
        os.system("taskkill /F /IM node.exe /T >nul 2>&1")
        
        # Cuidado: isso mata processos python. 
        # Como o watcher roda em python, é necessário.
        os.system("taskkill /F /IM python.exe /T >nul 2>&1")
        
        print("👋 Fábrica desligada.")

if __name__ == "__main__":
    main()
