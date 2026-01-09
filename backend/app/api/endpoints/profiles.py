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
    # Usando o Session Manager como fonte única da verdade
    # Usando o Session Manager como fonte única da verdade
    from backend.core.session_manager import list_available_sessions
    return list_available_sessions()

# Alias root para list
@router.get("/", response_model=List[Dict[str, str]])
async def get_profiles_root():
    return await get_profiles()

from pydantic import BaseModel

class ImportProfileRequest(BaseModel):
    label: str
    cookies: str

@router.post("/import")
async def import_profile_endpoint(request: ImportProfileRequest):
    """
    Importa um novo perfil a partir de um JSON de cookies.
    """
    from fastapi import HTTPException
    from backend.core.session_manager import import_session
    
    try:
        profile_id = import_session(request.label, request.cookies)
        return {"status": "success", "id": profile_id, "message": "Perfil importado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate/{profile_id}")
async def validate_profile_endpoint(profile_id: str):
    """
    Lança um navegador headless para extrair avatar e nome reais do TikTok.
    """
    import subprocess
    import sys
    import json
    from fastapi import HTTPException
    
    script_path = os.path.join(BASE_DIR, "core", "validator_cli.py")
    
    try:
        # Run subprocess to isolate event loop (fix for Windows + Uvicorn)
        result_proc = subprocess.run(
            [sys.executable, script_path, profile_id],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result_proc.returncode != 0:
            raise Exception(f"Script Error: {result_proc.stderr}")
            
        output = result_proc.stdout.strip()
        # Extract JSON from output (handle potential log noise)
        start_idx = output.find("{")
        end_idx = output.rfind("}")
        
        if start_idx != -1 and end_idx != -1:
            json_str = output[start_idx:end_idx+1]
            result = json.loads(json_str)
        else:
            raise Exception(f"No valid JSON in output: {output}")

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


