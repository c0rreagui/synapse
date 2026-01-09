
import requests
import json

BASE_URL = "http://localhost:8000"

def check_endpoint(method, path, expected_status=200):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url)
        
        if resp.status_code == expected_status:
           print(f"  🟢 [OK] {method} {path} -> {resp.status_code}")
           return True
        else:
           print(f"  🔴 [ERRO] {method} {path} -> {resp.status_code} (Esperado: {expected_status})")
           return False
    except Exception as e:
        print(f"  ❌ [FALHA] {method} {path} -> Erro de conexão: {e}")
        return False

if __name__ == "__main__":
    print("🩺 API Health Check")
    check_endpoint("GET", "/") # Root (geralmente 404 ou doc)
    check_endpoint("GET", "/api/v1/queue/pending", 200)
    check_endpoint("GET", "/docs", 200)
    check_endpoint("GET", "/openapi.json", 200)
