"""
VNC Fábrica — endpoints para criar novos perfis TikTok via sessão VNC interativa.

Fluxo:
1. POST /start   — abre browser limpo (sem cookies) no TikTok login com proxy selecionado
2. (operador faz login manualmente via VNC)
3. POST /capture — lê cookies do contexto ativo, cria perfil no DB, vincula proxy, encerra VNC
4. POST /stop    — encerra sessão factory sem capturar (descarta cookies)
"""
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class StartFactoryRequest(BaseModel):
    proxy_id: int


class CaptureFactoryRequest(BaseModel):
    label: Optional[str] = None
    proxy_id: Optional[int] = None


@router.get("/status")
async def factory_session_status():
    """Retorna o status da sessão VNC ativa (factory ou profile)."""
    from core.remote_session import get_session_status
    return get_session_status()


@router.post("/start")
async def factory_session_start(request: StartFactoryRequest):
    """
    Inicia uma sessão VNC fábrica com browser limpo no TikTok login.

    Requer proxy_id válido. Retorna novnc_url para acesso via browser.
    Retorna 409 se já houver uma sessão ativa.
    """
    from core.remote_session import start_factory_session

    host_url = os.environ.get("VPS_HOST", "localhost")
    result = await start_factory_session(
        proxy_id=request.proxy_id,
        host_url=host_url,
    )

    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])

    return result


@router.post("/capture")
async def factory_session_capture(request: CaptureFactoryRequest):
    """
    Captura o perfil TikTok logado da sessão fábrica ativa.

    Lê cookies do contexto Playwright, valida sessionid, busca info do usuário,
    cria registro no DB com proxy vinculado e encerra o VNC.

    Retorna 409 se não houver sessão fábrica ativa.
    Retorna 422 se o login ainda não foi concluído (sem cookie sessionid).
    """
    from core.remote_session import capture_factory_profile

    try:
        result = await capture_factory_profile(
            label=request.label,
            proxy_id=request.proxy_id,
        )
    except RuntimeError as e:
        msg = str(e)
        if "sessionid" in msg or "login" in msg.lower() or "Cookie" in msg:
            raise HTTPException(status_code=422, detail=msg)
        raise HTTPException(status_code=409, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao capturar perfil: {str(e)}")

    return result


@router.post("/stop")
async def factory_session_stop():
    """
    Encerra a sessão fábrica ativa sem capturar.
    Todos os cookies e o contexto do browser são descartados.

    Retorna 409 se a sessão ativa não for do tipo factory.
    """
    from core.remote_session import get_session_status, stop_session

    status = get_session_status()
    if not status.get("active"):
        return {"message": "Nenhuma sessão ativa.", "active": False}

    if status.get("session_type") != "factory":
        raise HTTPException(
            status_code=409,
            detail="A sessão ativa não é uma sessão fábrica. Use /api/v1/profiles/remote-session/stop.",
        )

    return stop_session()
