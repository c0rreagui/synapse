
import requests
import time

API_URL = "http://localhost:8000/api/v1/queue/approve"

videos = [
    {"filename": "audit_mass_01.mp4", "date": "2026-01-20T15:00"},
    {"filename": "audit_mass_02.mp4", "date": "2026-01-21T15:00"},
    {"filename": "audit_mass_03.mp4", "date": "2026-01-22T15:00"},
]

def approve_mass():
    print("🚀 Simulando Aprovação em Massa (Frontend -> Backend)...")
    
    for vid in videos:
        payload = {
            "id": vid["filename"],
            "action": "scheduled",
            "schedule_time": vid["date"]
        }
        
        try:
            print(f"  👉 Enviando {vid['filename']} para {vid['date']}...")
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                print(f"     ✅ Sucesso: {response.json()}")
            else:
                print(f"     ❌ Falha ({response.status_code}): {response.text}")
                
        except Exception as e:
            print(f"     ❌ Erro de conexão: {e}")
            
        time.sleep(1) # Simula delay natural do frontend loop

    print("🏁 Disparos concluídos.")

if __name__ == "__main__":
    approve_mass()
