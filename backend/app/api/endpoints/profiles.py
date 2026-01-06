import os
import glob
from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

# Caminho para a pasta de sessões
# backend/app/api/endpoints/profiles.py -> backend/app/api/endpoints -> backend/app/api -> backend/app -> backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Adjusting to backend/data/sessions
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")

@router.get("/list", response_model=List[Dict[str, str]])
async def get_profiles():
    """
    Lista os arquivos de sessão JSON disponíveis na pasta de dados.
    Retorna uma lista formatada para o Frontend.
    """
    # Fallback/Mock se a pasta não existir ou estiver vazia
    # Garante que a UI sempre tenha algo para mostrar no MVP
    default_profiles = [
        {"id": "tiktok_profile_01", "label": "✂️ Cortes Aleatórios (@p1)"},
        {"id": "tiktok_profile_02", "label": "🔥 Criando Ibope (@p2)"}
    ]
    
    # Tenta ler do disco real
    real_sessions = []
    
    if os.path.exists(SESSIONS_DIR):
        try:
            for filename in os.listdir(SESSIONS_DIR):
                if filename.endswith(".json") and filename.startswith("tiktok_profile"):
                    profile_id = filename.replace(".json", "")
                    
                    # Formata o label para ficar amigável
                    clean_name = profile_id.replace("tiktok_profile_", "").replace("_", " ").title()
                    label = f"Perfil {clean_name}"
                    
                    if "01" in profile_id: label = f"✂️ {label} (Cortes)"
                    if "02" in profile_id: label = f"🔥 {label} (Ibope)"
                    
                    real_sessions.append({
                        "id": profile_id,
                        "label": label
                    })
            # Se achou algo real, prioriza. Se não, retorna default para não quebrar UI
            if real_sessions:
                # Opcional: Merge com default ou usar apenas real.
                # Para MVP, se achou real, usa real.
                real_sessions.sort(key=lambda x: x['id'])
                return real_sessions
                
        except Exception as e:
            print(f"Error scanning sessions: {e}")
            
    # Retorna defaults se não achou nada ou deu erro
    return default_profiles

# Alias root para list
@router.get("/", response_model=List[Dict[str, str]])
async def get_profiles_root():
    return await get_profiles()
