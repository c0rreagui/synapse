from fastapi import APIRouter
import os
import glob
import sys
from typing import List, Dict

# Ajuste de path para importar core
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from core import tiktok_profile

router = APIRouter()

SESSIONS_DIR = os.path.join(BACKEND_DIR, "data", "sessions")

@router.get("/", response_model=List[Dict[str, str]])
async def get_profiles():
    """
    Lista os perfis disponíveis e enriquece com dados reais do TikTok (nome, avatar).
    """
    if not os.path.exists(SESSIONS_DIR):
        return []

    profiles = []
    
    # Busca arquivos json que começam com tiktok_profile
    for session_file in glob.glob(os.path.join(SESSIONS_DIR, "tiktok_profile_*.json")):
        filename = os.path.basename(session_file)
        profile_id = os.path.splitext(filename)[0]
        
        # Tenta enriquecer metadados (cacheado)
        # DESABILITADO POR SOLICITAÇÃO DO USUÁRIO (DADOS INCORRETOS)
        # meta = tiktok_profile.enrich_session_metadata(session_file)
        
        display_name = ""
        username = ""
        avatar = ""
        
        # if meta:
        #     display_name = meta.get("display_name")
        #     username = meta.get("username")
        #     avatar = meta.get("avatar_url")
            
        # Fallback sempre ativo agora (Baseado no nome do arquivo)
        if not display_name:
            # tiktok_profile_01 -> Perfil 01
            # tiktok_profile_cortes -> Perfil Cortes
            clean_name = profile_id.replace("tiktok_profile_", "").replace("_", " ").title()
            display_name = f"Perfil {clean_name}" if clean_name.isdigit() else clean_name

        # Gera ID curto para compatibilidade (tiktok_profile_01 -> p1)
        # Remove zeros à esquerda dos números para ficar p1, p2 etc.
        short_id = profile_id.replace("tiktok_profile_", "p")
        if short_id.startswith("p0"):
            short_id = short_id.replace("p0", "p")

        profiles.append({
            "id": short_id, # Frontend usa este ID curto (p1, p2)
            "name": display_name,
            "username": username,
            "avatar": avatar,
            "filename": filename
        })
    
    # Ordena pelo nome
    profiles.sort(key=lambda x: x["name"])
    
    return profiles
