"""
Session Keepalive — Mantém sessões TikTok vivas automaticamente.

Problema: Sessões TikTok expiram se ficam inativas. Se o perfil não faz uploads
por alguns dias, os cookies morrem e é preciso login manual (VNC).

Solução: Fazer pings HTTP periódicos ao TikTok usando os cookies e proxy de cada
perfil. Isso mantém a sessão ativa e captura cookies atualizados dos headers
Set-Cookie da resposta.

Frequência: A cada 4 horas (configuraível via KEEPALIVE_INTERVAL_HOURS).
"""

import os
import json
import time
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional

logger = logging.getLogger("SessionKeepalive")

KEEPALIVE_INTERVAL_HOURS = 4
TIKTOK_PING_URLS = [
    "https://www.tiktok.com/tiktokstudio",
    "https://www.tiktok.com/",
]

# Track last keepalive per profile to avoid hammering
_last_keepalive: Dict[str, float] = {}


async def keepalive_all_profiles() -> Dict[str, Any]:
    """
    Faz keepalive de todos os perfis ativos.
    Retorna resumo: {refreshed: [...], expired: [...], errors: [...]}.
    """
    from core.session_manager import list_available_sessions

    profiles = list_available_sessions()
    active_profiles = [p for p in profiles if p.get("status") == "active"]

    if not active_profiles:
        logger.debug("Keepalive: nenhum perfil ativo encontrado")
        return {"refreshed": [], "expired": [], "errors": []}

    results = {"refreshed": [], "expired": [], "errors": []}

    for profile in active_profiles:
        profile_id = profile.get("id")
        if not profile_id:
            continue

        # Verificar intervalo — não fazer keepalive se fez recentemente
        last = _last_keepalive.get(profile_id, 0)
        elapsed_hours = (time.time() - last) / 3600
        if elapsed_hours < KEEPALIVE_INTERVAL_HOURS:
            continue

        try:
            result = await keepalive_profile(profile_id)
            if result["status"] == "alive":
                results["refreshed"].append(profile_id)
            elif result["status"] == "expired":
                results["expired"].append(profile_id)
            else:
                results["errors"].append({"profile": profile_id, "error": result.get("error")})
        except Exception as e:
            logger.error(f"Keepalive falhou para {profile_id}: {e}")
            results["errors"].append({"profile": profile_id, "error": str(e)})

    if results["refreshed"]:
        logger.info(f"🔄 Keepalive: {len(results['refreshed'])} perfis renovados")
    if results["expired"]:
        logger.warning(f"⚠️ Keepalive: {len(results['expired'])} perfis com sessão expirada: {results['expired']}")

    return results


async def keepalive_profile(profile_id: str) -> Dict[str, Any]:
    """
    Faz ping no TikTok com os cookies e proxy de um perfil.
    Se a sessão estiver viva, atualiza os cookies salvos.
    Se estiver morta, marca o perfil como inativo.
    """
    import httpx
    from core.session_manager import get_session_path
    from core.network_utils import get_profile_identity

    session_path = get_session_path(profile_id)
    if not os.path.exists(session_path):
        return {"status": "error", "error": "Arquivo de sessão não encontrado"}

    # Carregar cookies e identidade
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        cookies_list = session_data.get("cookies", []) if isinstance(session_data, dict) else session_data
        meta = session_data.get("synapse_meta", {}) if isinstance(session_data, dict) else {}
    except Exception as e:
        return {"status": "error", "error": f"Erro ao ler sessão: {e}"}

    # Montar cookies dict para httpx
    cookies_dict = {}
    for c in cookies_list:
        if isinstance(c, dict) and c.get("name") and c.get("value"):
            # Só incluir cookies do domínio tiktok
            domain = c.get("domain", "")
            if "tiktok" in domain:
                cookies_dict[c["name"]] = c["value"]

    if "sessionid" not in cookies_dict:
        logger.warning(f"[KEEPALIVE] {profile_id}: sem cookie sessionid")
        return {"status": "expired", "error": "Cookie sessionid ausente"}

    # Resolver proxy e UA
    identity = get_profile_identity(profile_id)
    user_agent = identity.get("user_agent") or meta.get("user_agent")

    # Configurar proxy para httpx
    proxy_url = None
    if identity.get("proxy"):
        proxy = identity["proxy"]
        if isinstance(proxy, dict) and proxy.get("server"):
            server = proxy["server"]
            username = proxy.get("username", "")
            password = proxy.get("password", "")
            if username and password:
                # http://user:pass@host:port
                proto = "http"
                host_part = server.replace("http://", "").replace("https://", "")
                proxy_url = f"{proto}://{username}:{password}@{host_part}"
            else:
                proxy_url = server

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    # Fazer o ping
    session_alive = False
    new_cookies = {}

    for url in TIKTOK_PING_URLS:
        try:
            transport = httpx.AsyncHTTPTransport(proxy=proxy_url) if proxy_url else None
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=15.0,
                transport=transport,
            ) as client:
                response = await client.get(url, cookies=cookies_dict, headers=headers)

                final_url = str(response.url).lower()

                # Verificar se foi redirecionado para login
                if "login" in final_url or "passport" in final_url:
                    logger.info(f"[KEEPALIVE] {profile_id}: redirecionado para login em {url}")
                    continue

                if "onelink.me" in final_url:
                    logger.info(f"[KEEPALIVE] {profile_id}: redirecionado para app store")
                    continue

                # Sessão viva — capturar cookies da resposta
                if response.status_code == 200:
                    session_alive = True

                    # Extrair cookies atualizados de todos os responses na cadeia de redirects
                    for cookie_name, cookie_value in response.cookies.items():
                        new_cookies[cookie_name] = cookie_value

                    logger.info(f"[KEEPALIVE] {profile_id}: sessão viva ✓ ({len(new_cookies)} cookies atualizados)")
                    break

        except httpx.TimeoutException:
            logger.warning(f"[KEEPALIVE] {profile_id}: timeout em {url}")
            continue
        except Exception as e:
            logger.warning(f"[KEEPALIVE] {profile_id}: erro em {url}: {e}")
            continue

    # Registrar timestamp do keepalive
    _last_keepalive[profile_id] = time.time()

    if session_alive:
        # Atualizar cookies no arquivo de sessão
        if new_cookies:
            _merge_cookies(session_path, cookies_list, new_cookies)

        # Garantir que perfil está ativo
        from core.session_manager import update_profile_status
        update_profile_status(profile_id, True)

        return {"status": "alive", "cookies_updated": len(new_cookies)}
    else:
        # Sessão morta — marcar perfil
        logger.warning(f"[KEEPALIVE] {profile_id}: sessão expirada — necessário reconectar")
        from core.session_manager import update_profile_status
        update_profile_status(profile_id, False)

        return {"status": "expired", "error": "Sessão TikTok expirada"}


def _merge_cookies(session_path: str, existing_cookies: list, new_cookies: Dict[str, str]):
    """
    Merge cookies novos (do response HTTP) no arquivo de sessão existente.
    Atualiza valores de cookies existentes e adiciona novos.
    """
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        cookies_list = session_data.get("cookies", []) if isinstance(session_data, dict) else session_data

        # Criar index por nome para update rápido
        cookie_index = {}
        for i, c in enumerate(cookies_list):
            if isinstance(c, dict) and c.get("name"):
                cookie_index[c["name"]] = i

        updated = 0
        for name, value in new_cookies.items():
            if name in cookie_index:
                # Atualizar cookie existente
                idx = cookie_index[name]
                if cookies_list[idx].get("value") != value:
                    cookies_list[idx]["value"] = value
                    updated += 1
            else:
                # Cookie novo — adicionar com defaults do TikTok
                cookies_list.append({
                    "name": name,
                    "value": value,
                    "domain": ".tiktok.com",
                    "path": "/",
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "None",
                })
                updated += 1

        if updated > 0:
            if isinstance(session_data, dict):
                session_data["cookies"] = cookies_list
            else:
                session_data = {"cookies": cookies_list, "origins": []}

            # Registrar timestamp do refresh nos metadados
            if isinstance(session_data, dict):
                if "synapse_meta" not in session_data:
                    session_data["synapse_meta"] = {}
                session_data["synapse_meta"]["last_keepalive"] = datetime.now(
                    ZoneInfo("America/Sao_Paulo")
                ).isoformat()

            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)

            logger.debug(f"[KEEPALIVE] {updated} cookies atualizados em {os.path.basename(session_path)}")

    except Exception as e:
        logger.error(f"[KEEPALIVE] Erro ao salvar cookies: {e}")
