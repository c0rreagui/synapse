import subprocess
import time
import os
import sys

def main():
    print("--- 🔌 INICIANDO SYNAPSE (MODO DIRETO + UTF-8) ---")
    
    # Derivar caminhos absolutos baseados na localização do script
    # Script está em tools/ignite.py -> parent é tools -> grantparent é root
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
    FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
    
    # Lista para guardar os processos
    processes = []
    
    try:
        # 1. API (Backend)
        # stdout=None faz o log sair direto no terminal, sem passar pelo Python (Zero erro de encoding)
        print(">>> Lançando API...")
        
        env = os.environ.copy()
        # Adiciona o root ao PYTHONPATH para garantir que imports funcionem
        env["PYTHONPATH"] = ROOT_DIR + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
        
        # Agora usamos cwd absoluto para o backend
        p_api = subprocess.Popen("uvicorn app.main:app --reload --port 8000", cwd=BACKEND_DIR, shell=True, env=env)
        processes.append(p_api)
        time.sleep(2) # Dá um tempinho pra API respirar

        # 2. Frontend (Web)
        print(">>> Lançando Frontend...")
        p_web = subprocess.Popen("npm run dev", cwd=FRONTEND_DIR, shell=True, env=env)
        processes.append(p_web)

        # 3. Watcher (Robô)
        print(">>> Lançando Robô Watcher...")
        # Robô roda a partir do root
        p_bot = subprocess.Popen("python backend/core/factory_watcher.py", cwd=ROOT_DIR, shell=True, env=env)
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
