
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


# ─── SYN-88: Bulk Endpoints ─────────────────────────────────────────────

class BulkProfileRequest(BaseModel):
    profile_ids: List[str]


@router.post("/bulk-refresh")
async def bulk_refresh_endpoint(request: BulkProfileRequest, background_tasks: BackgroundTasks):
    """
    Refresh de metadados (avatar, status) em lote.
    Enfileira cada perfil sequencialmente no background para evitar
    race conditions no SQLite com múltiplos threads simultâneos.
    """
    from fastapi.concurrency import run_in_threadpool
    from core.session_manager import update_profile_metadata_async

    if not request.profile_ids:
        raise HTTPException(status_code=400, detail="Lista de profile_ids vazia")

    for pid in request.profile_ids:
        background_tasks.add_task(run_in_threadpool, update_profile_metadata_async, pid)

    return {
        "status": "refreshing",
        "count": len(request.profile_ids),
        "message": f"Refresh iniciado para {len(request.profile_ids)} perfis em background.",
    }


@router.post("/bulk-delete")
async def bulk_delete_endpoint(request: BulkProfileRequest):
    """
    Deleção em lote de perfis.
    Loop transacional interno: deleta um a um dentro do mesmo request,
    evitando race conditions de 'Database is locked' no SQLite.
    """
    from core.session_manager import delete_session

    if not request.profile_ids:
        raise HTTPException(status_code=400, detail="Lista de profile_ids vazia")

    results = {"deleted": [], "failed": []}

    for pid in request.profile_ids:
        try:
            success = delete_session(pid)
            if success:
                results["deleted"].append(pid)
            else:
                results["failed"].append({"id": pid, "reason": "Perfil não encontrado"})
        except Exception as e:
            results["failed"].append({"id": pid, "reason": str(e)})

    return {
        "status": "completed",
        "deleted_count": len(results["deleted"]),
        "failed_count": len(results["failed"]),
        "details": results,
    }


# ─── SYN-83: Proxy Management per Profile ────────────────────────────────

class ProxyConfigRequest(BaseModel):
    proxy_server: str           # Ex: "http://123.45.67.89:8080"
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None


@router.get("/{profile_id}/proxy")
async def get_proxy_config(profile_id: str):
    """
    Retorna a configuração de proxy de um perfil.
    Mascara a senha por segurança.
    """
    from core.database import SessionLocal
    from core.models import Profile
    from fastapi.concurrency import run_in_threadpool

    def _get():
        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(
                (Profile.slug == profile_id) | (Profile.username == profile_id)
            ).first()
            if not profile:
                return None
            return {
                "proxy_server": profile.proxy_server,
                "proxy_username": profile.proxy_username,
                "proxy_password": ("***" + profile.proxy_password[-4:]) if profile.proxy_password and len(profile.proxy_password) > 4 else ("***" if profile.proxy_password else None),
                "has_proxy": bool(profile.proxy_server),
            }
        finally:
            db.close()

    result = await run_in_threadpool(_get)
    if result is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return result


@router.put("/{profile_id}/proxy")
async def set_proxy_config(profile_id: str, request: ProxyConfigRequest):
    """
    Define ou atualiza o proxy de um perfil.
    """
    from core.database import SessionLocal
    from core.models import Profile
    from fastapi.concurrency import run_in_threadpool

    def _update():
        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(
                (Profile.slug == profile_id) | (Profile.username == profile_id)
            ).first()
            if not profile:
                return False
            profile.proxy_server = request.proxy_server
            profile.proxy_username = request.proxy_username
            profile.proxy_password = request.proxy_password
            db.commit()
            return True
        finally:
            db.close()

    success = await run_in_threadpool(_update)
    if not success:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return {"status": "success", "message": f"Proxy configurado para {profile_id}"}


@router.delete("/{profile_id}/proxy")
async def remove_proxy_config(profile_id: str):
    """
    Remove o proxy de um perfil (limpa todas as credenciais).
    """
    from core.database import SessionLocal
    from core.models import Profile
    from fastapi.concurrency import run_in_threadpool

    def _clear():
        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(
                (Profile.slug == profile_id) | (Profile.username == profile_id)
            ).first()
            if not profile:
                return False
            profile.proxy_server = None
            profile.proxy_username = None
            profile.proxy_password = None
            db.commit()
            return True
        finally:
            db.close()

    success = await run_in_threadpool(_clear)
    if not success:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return {"status": "success", "message": f"Proxy removido de {profile_id}"}


@router.post("/{profile_id}/test-proxy")
async def test_proxy_config(profile_id: str):
    """
    Testa a conectividade do proxy configurado para um perfil.
    Faz um GET em https://httpbin.org/ip via o proxy para verificar se funciona.
    """
    import httpx
    from core.database import SessionLocal
    from core.models import Profile
    from fastapi.concurrency import run_in_threadpool

    def _get_proxy():
        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(
                (Profile.slug == profile_id) | (Profile.username == profile_id)
            ).first()
            if not profile:
                return None
            if not profile.proxy_server:
                return {"error": "Nenhum proxy configurado"}
            return {
                "server": profile.proxy_server,
                "username": profile.proxy_username,
                "password": profile.proxy_password,
            }
        finally:
            db.close()

    proxy_info = await run_in_threadpool(_get_proxy)
    if proxy_info is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    if "error" in proxy_info:
        raise HTTPException(status_code=400, detail=proxy_info["error"])

    # Build proxy URL
    server = proxy_info["server"]
    if proxy_info.get("username") and proxy_info.get("password"):
        # Insert auth into URL: http://user:pass@host:port
        protocol = "http://"
        if server.startswith("http://"):
            server = server[7:]
        elif server.startswith("https://"):
            protocol = "https://"
            server = server[8:]
        proxy_url = f"{protocol}{proxy_info['username']}:{proxy_info['password']}@{server}"
    else:
        proxy_url = server

    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
            resp = await client.get("https://httpbin.org/ip")
            data = resp.json()
            return {
                "status": "success",
                "proxy_ip": data.get("origin", "unknown"),
                "message": f"Proxy funcional. IP: {data.get('origin', '?')}",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Proxy falhou: {str(e)}",
        }
