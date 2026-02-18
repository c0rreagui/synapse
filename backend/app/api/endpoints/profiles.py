
import os
import glob
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from .. import websocket

router = APIRouter()

# Caminho para a pasta de sessões
# backend/app/api/endpoints/profiles.py -> backend/app/api/endpoints -> backend/app/api -> backend/app -> backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Adjusting to backend/data/sessions
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")

@router.get("/list", response_model=List[Dict[str, Any]])
async def get_profiles():
    """
    Lista os arquivos de sessão JSON disponíveis na pasta de dados.
    Retorna uma lista formatada para o Frontend.
    """
    # Usando o Session Manager como fonte única da verdade
    from core.session_manager import list_available_sessions
    from fastapi.concurrency import run_in_threadpool
    return await run_in_threadpool(list_available_sessions)

# Alias root para list
@router.get("/", response_model=List[Dict[str, Any]])
async def get_profiles_root():
    return await get_profiles()

from pydantic import BaseModel

class ImportProfileRequest(BaseModel):
    label: str | None = None
    cookies: str
    username: str | None = None
    avatar_url: str | None = None

@router.post("/import")
async def import_profile_endpoint(request: ImportProfileRequest, background_tasks: BackgroundTasks):
    """
    Importa um novo perfil a partir de um JSON de cookies.
    Se o label não for fornecido, tenta extrair dos cookies.
    """
    from fastapi import HTTPException
    from fastapi.concurrency import run_in_threadpool
    from core.session_manager import import_session, get_profile_metadata, update_profile_metadata_async
    
    try:
        # Se label for None, import_session vai gerar um temporário
        profile_id = await run_in_threadpool(import_session, request.label, request.cookies, request.username, request.avatar_url)
        
        # Trigger background metadata fetch
        background_tasks.add_task(run_in_threadpool, update_profile_metadata_async, profile_id)

    except Exception as e:
        # Simplificando erro
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"profile_id": profile_id, "status": "imported", "message": "Importação iniciada. Metadados serão atualizados em breve."}


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
            # Try to parse error from stdout if available, else stderr
            try:
               res_err = json.loads(result_proc.stdout)
               return res_err
            except:
               raise HTTPException(status_code=500, detail=f"Validator Script Failed: {result_proc.stderr}")

        try:
            result = json.loads(result_proc.stdout)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"Validator Output Invalid: '{result_proc.stdout}' Stderr: {result_proc.stderr}")

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        # Notify
        from core.session_manager import get_profile_metadata
        profile_data = get_profile_metadata(profile_id)
        if profile_data:
            await websocket.notify_profile_change(profile_data)

        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.post("/repair/{profile_id}")
async def repair_session_endpoint(profile_id: str, background_tasks: BackgroundTasks):
    """
    Launches an interactive browser for manual session repair.
    The browser opens in the background and waits for user to log in.
    """
    from core.browser_manager import browser_manager
    from fastapi import HTTPException
    import asyncio
    
    # 1. Check if busy
    if browser_manager.is_busy(profile_id):
         raise HTTPException(status_code=409, detail=f"Profile {profile_id} is already busy (Repairing/Running).")

    # 2. Launch Repair in Background using asyncio.create_task
    # We need to run the async function in the existing event loop
    asyncio.create_task(browser_manager.launch_repair_session(profile_id))
    
    return {"status": "launched", "message": "Browser aberto no servidor. Faca login manualmente e depois feche o navegador."}


@router.post("/refresh-avatar/{profile_id}")
async def refresh_avatar_endpoint(profile_id: str, background_tasks: BackgroundTasks):
    """
    Inicia o refresh do avatar e metadados em background usando a API/Scraper.
    """
    from fastapi.concurrency import run_in_threadpool
    from core.session_manager import update_profile_metadata_async
    
    # [SYN-FIX] Substituído validator_cli (que só valida login) por update_metadata (que baixa avatar)
    background_tasks.add_task(run_in_threadpool, update_profile_metadata_async, profile_id)
    
    return {"status": "refreshing", "message": "Avatar e metadados estão sendo atualizados em background."}
class UpdateCookiesRequest(BaseModel):
    cookies: str

@router.put("/{profile_id}/cookies")
async def update_cookies_endpoint(profile_id: str, request: UpdateCookiesRequest):
    """
    Atualiza os cookies de um perfil existente.
    Usado para renovar sessões expiradas sem criar novo perfil.
    """
    from core.session_manager import update_session_cookies
    from fastapi.concurrency import run_in_threadpool
    
    success = await run_in_threadpool(update_session_cookies, profile_id, request.cookies)
    
    if not success:
        raise HTTPException(status_code=400, detail="Falha ao atualizar cookies. Verifique se o perfil existe.")
        
    return {"status": "success", "message": "Cookies atualizados com sucesso."}

@router.delete("/{profile_id}")
async def delete_profile_endpoint(profile_id: str):
    """
    Remove um perfil do sistema (banco de dados e arquivo de sessão).
    """
    from fastapi import HTTPException
    from core.session_manager import delete_session
    
    success = delete_session(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Perfil não encontrado ou erro ao excluir")
        
    return {"status": "success", "message": f"Perfil {profile_id} removido."}

