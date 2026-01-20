import os
import glob
from fastapi import APIRouter
from typing import List, Dict
from .. import websocket

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
    from core.session_manager import list_available_sessions
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
    from core.session_manager import import_session
    
    try:
        profile_id = import_session(request.label, request.cookies)
        
        # Notify
        from core.session_manager import get_profile_metadata
        profile_data = get_profile_metadata(profile_id)
        if profile_data:
            await websocket.notify_profile_change(profile_data)

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
            
        # Notify
        from core.session_manager import get_profile_metadata
        profile_data = get_profile_metadata(profile_id)
        if profile_data:
            await websocket.notify_profile_change(profile_data)

        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-avatar/{profile_id}")
async def refresh_avatar_endpoint(profile_id: str):
    """
    Busca o avatar atualizado do TikTok para um perfil.
    Usa Playwright para acessar o perfil e extrair a nova URL do avatar.
    """
    from fastapi import HTTPException
    from core.session_manager import get_profile_metadata, update_profile_metadata
    from core.browser import launch_browser, close_browser
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get current profile data
    metadata = get_profile_metadata(profile_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Perfil {profile_id} não encontrado")
    
    username = metadata.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Perfil não tem username definido")
    
    logger.info(f"🔄 Refreshing avatar for @{username}...")
    
    try:
        p, browser, context, page = await launch_browser(
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        try:
            # Navigate to profile
            url = f"https://www.tiktok.com/@{username}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Wait for avatar to load
            await page.wait_for_timeout(3000)
            
            # Try multiple selectors for avatar (TikTok changes these often)
            avatar_selectors = [
                '[data-e2e="user-avatar"] img',
                '.css-1zpj2q-ImgAvatar img',
                'img[class*="Avatar"]',
                '.share-avatar img',
                'img[src*="tiktokcdn.com"][src*="avt"]'
            ]
            
            new_avatar_url = None
            for selector in avatar_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        new_avatar_url = await page.locator(selector).first.get_attribute("src")
                        if new_avatar_url and "tiktokcdn.com" in new_avatar_url:
                            logger.info(f"✅ Found avatar with selector: {selector}")
                            break
                except:
                    continue
            
            if not new_avatar_url:
                raise HTTPException(status_code=404, detail="Não foi possível encontrar avatar no perfil")
            
            # Update profile metadata
            old_avatar = metadata.get("avatar_url", "")
            update_profile_metadata(profile_id, {"avatar_url": new_avatar_url})
            
            logger.info(f"✅ Avatar atualizado para @{username}")
            
            # Notify
            updated_profile = get_profile_metadata(profile_id)
            if updated_profile:
                await websocket.notify_profile_change(updated_profile)

            return {
                "status": "success",
                "profile_id": profile_id,
                "username": username,
                "avatar_url": new_avatar_url,
                "previous_url": old_avatar[:50] + "..." if len(old_avatar) > 50 else old_avatar
            }
            
        finally:
            await close_browser(p, browser)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))
