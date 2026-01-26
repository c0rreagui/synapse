import os
import sys
import requests
import json
import psutil
import subprocess
from datetime import datetime
from pathlib import Path

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Config
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
LOG_FILE = "backend/gods_eye_report.txt"

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def check_port(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            return True
    return False

def check_docker_container(name):
    try:
        res = subprocess.run(["docker", "inspect", "-f", "{{.State.Status}}", name], capture_output=True, text=True)
        if res.returncode == 0:
            status = res.stdout.strip()
            return status == "running", status
    except:
        pass
    return False, "unknown"

def scan_logs_for_errors(container_name):
    try:
        res = subprocess.run(["docker", "logs", "--tail", "200", container_name], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if res.returncode == 0:
            logs = res.stdout + res.stderr
            errors = [line for line in logs.splitlines() if "ERROR" in line or "CRITICAL" in line or "Exception" in line]
            return errors
    except Exception as e:
        return [f"Log fetch failed: {str(e)}"]
    return []

def main():
    log("👁️ INICIANDO O OLHO QUE TUDO VÊ (Diagnostic Scan) 👁️")
    log("====================================================")
    
    # 1. Infrastructure Checks
    log("🔍 Checando Infraestrutura...")
    
    # Frontend
    fe_alive, fe_status = check_docker_container("synapse-frontend")
    if fe_alive:
        log("✅ Frontend Container: ONLINE")
    else:
        log(f"❌ Frontend Container: {fe_status}", "CRITICAL")
        
    # Backend
    be_alive, be_status = check_docker_container("synapse-backend")
    if be_alive:
        log("✅ Backend Container: ONLINE")
    else:
        log(f"❌ Backend Container: {fe_status}", "CRITICAL")
        
    # 2. API Health Checks (Integration)
    log("\n🔍 Checando API Endpoints...")
    
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/ingest/status", timeout=5)
        if r.status_code == 200:
            log(f"✅ API Health Check: OK ({r.elapsed.total_seconds()}s)")
        else:
            log(f"❌ API Health Check: FAIL ({r.status_code})", "ERROR")
    except Exception as e:
        log(f"❌ API Connection Failed: {str(e)}", "CRITICAL")
        
    # 3. Database / Session Check
    log("\n🔍 Checando Sessões/Profiles...")
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/profiles/list", timeout=5)
        if r.status_code == 200:
            profiles = r.json()
            log(f"✅ Profiles Endpoint: OK (Found {len(profiles)} profiles)")
            if len(profiles) == 0:
                log("⚠️ Nenhuma sessão encontrada. Verifique se o diretório 'data/sessions' está mapeado.", "WARNING")
        else:
            log(f"❌ Profiles Endpoint: FAIL ({r.status_code})", "ERROR")
            
            # Diagnóstico de Redirecionamento 307
            if r.status_code == 307:
                 log(f"⚠️ Redirect 307 Detectado no endpoint. Use '/list' explícito.", "WARNING")

    except Exception as e:
        log(f"❌ API Profiles Failed: {str(e)}", "ERROR")

    # 4. Log Analysis
    log("\n🔍 Analisando Logs Recentes (Backend)...")
    errors = scan_logs_for_errors("synapse-backend")
    if not errors:
        log("✅ Nenhum erro crítico recente nos logs.")
    else:
        log(f"⚠️ Encontrados {len(errors)} erros recentes:", "WARNING")
        for err in errors[-5:]: # Show last 5
            log(f"   > {err.strip()}", "ERROR_TRACE")

    log("\n====================================================")
    log("👁️ SCAN CONCLUÍDO.")

if __name__ == "__main__":
    main()
