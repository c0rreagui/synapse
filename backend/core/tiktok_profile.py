import json
import os
import logging
import requests
import re
import time
from datetime import datetime
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

def load_session_data(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao ler sessão {path}: {e}")
        return None

def save_session_data(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar sessão {path}: {e}")
        return False

def extract_cookies_dict(session_data):
    """Converte lista de cookies do Playwright para dict simples requests"""
    if 'cookies' in session_data:
        cookies = {}
        for c in session_data['cookies']:
            cookies[c['name']] = c['value']
        return cookies
    return None

def fetch_tiktok_user_info(cookies, proxy_url=None):
    """
    Busca informações do usuário logado.
    Estratégia com múltiplos fallbacks:
    1. Passport API (endpoint principal de account info)
    2. Passport API v2 (endpoint alternativo)
    3. Scrape da página pública (para avatar atualizado)
    """
    from core.network_utils import get_tiktok_headers, get_passport_api_url, get_random_user_agent

    handle = None
    display_name = None
    avatar_url = None

    # Build proxy dict for requests if provided
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
        logger.info(f"Using proxy for metadata fetch")

    # ── Strategy 1: Passport API (primary) ──
    headers_api = get_tiktok_headers()
    # [SYN-FIX] Remove Brotli (br) from Accept-Encoding — requests library
    # doesn't decode Brotli natively, causing garbled responses
    headers_api["Accept-Encoding"] = "gzip, deflate"
    url_api = get_passport_api_url()

    try:
        r = requests.get(url_api, cookies=cookies, headers=headers_api, timeout=10, proxies=proxies)
        logger.info(f"Passport API response: status={r.status_code}, body_len={len(r.content)}, content_type={r.headers.get('content-type', 'unknown')}")
        if r.status_code == 200:
            # Log raw content for debugging non-JSON responses
            raw = r.text.strip()
            if not raw or not raw.startswith('{'):
                logger.warning(f"Passport API returned non-JSON: {raw[:300]}")
            wrapper = json.loads(raw) if raw.startswith('{') else {}
            logger.info(f"Passport API keys: {list(wrapper.keys())}")

            # Try multiple response structures (TikTok changes these)
            passport_data = wrapper.get("data", {})
            if not passport_data and "user" in wrapper:
                passport_data = wrapper["user"]
            if not passport_data and "userInfo" in wrapper:
                passport_data = wrapper["userInfo"]

            if passport_data:
                logger.info(f"Passport data keys: {list(passport_data.keys())}")
                handle = (
                    passport_data.get("username") or
                    passport_data.get("unique_id") or
                    passport_data.get("uniqueId") or
                    passport_data.get("user_id_str", "")
                )
                display_name = (
                    passport_data.get("screen_name") or
                    passport_data.get("nickname") or
                    passport_data.get("display_name", "")
                )
                # Avatar: try flat string first, then nested object
                avatar_url = passport_data.get("avatar_url", "")
                if not avatar_url:
                    avatar_larger = passport_data.get("avatar_larger")
                    if isinstance(avatar_larger, dict):
                        url_list = avatar_larger.get("url_list", [])
                        if url_list:
                            avatar_url = url_list[0]
            else:
                logger.warning(f"Passport API returned empty data. Full response: {json.dumps(wrapper)[:500]}")
    except Exception as e:
        logger.warning(f"Passport API failed: {e}")

    # ── Strategy 2: TikTok Web API self-info ──
    if not handle:
        try:
            alt_url = "https://www.tiktok.com/api/user/detail/?WebIdLastTime=0&aid=1988&app_language=pt-BR&app_name=tiktok_web&device_platform=web_pc&from_page=user"
            r2 = requests.get(alt_url, cookies=cookies, headers=headers_api, timeout=10, proxies=proxies)
            logger.info(f"Alt API response: status={r2.status_code}, body_len={len(r2.content)}")
            if r2.status_code == 200:
                raw2 = r2.text.strip()
                if not raw2 or not raw2.startswith('{'):
                    logger.warning(f"Alt API returned non-JSON: {raw2[:300]}")
                data2 = json.loads(raw2) if raw2.startswith('{') else {}
                user_info = data2.get("userInfo", {}).get("user", {})
                if user_info:
                    handle = user_info.get("uniqueId") or user_info.get("unique_id", "")
                    display_name = user_info.get("nickname", "")
                    avatar_url = user_info.get("avatarLarger") or user_info.get("avatarMedium", "")
                    logger.info(f"Alt API found user: @{handle}")
        except Exception as e:
            logger.warning(f"Alt API failed: {e}")

    # ── Strategy 3: Scrape settings page (requires auth cookies) ──
    if not handle:
        try:
            settings_url = "https://www.tiktok.com/setting"
            headers_nav = {
                "User-Agent": get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.tiktok.com/",
            }
            r3 = requests.get(settings_url, cookies=cookies, headers=headers_nav, timeout=10, allow_redirects=True, proxies=proxies)
            logger.info(f"Settings page response: status={r3.status_code}, url={r3.url[:80]}")
            if r3.status_code == 200 and "login" not in r3.url:
                html = r3.text
                # Extract from NEXT_DATA or UNIVERSAL_DATA
                for script_id in ["__NEXT_DATA__", "__UNIVERSAL_DATA_FOR_REHYDRATION__", "SIGI_STATE"]:
                    pattern = rf'<script id="{script_id}" type="application/json">(.+?)</script>'
                    match = re.search(pattern, html)
                    if match:
                        try:
                            sdata = json.loads(match.group(1))
                            # Navigate common structures
                            user = None
                            if "props" in sdata:
                                user = sdata.get("props", {}).get("pageProps", {}).get("userInfo", {}).get("user", {})
                            elif "__DEFAULT_SCOPE__" in sdata:
                                user = sdata.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {}).get("user", {})
                            elif "UserModule" in sdata:
                                users = sdata.get("UserModule", {}).get("users", {})
                                if users:
                                    user = next(iter(users.values()), {})

                            if user and user.get("uniqueId"):
                                handle = user["uniqueId"]
                                display_name = user.get("nickname", "")
                                avatar_url = user.get("avatarLarger") or user.get("avatarMedium", "")
                                logger.info(f"Extracted user from {script_id}: @{handle}")
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Settings page scrape failed: {e}")

    # If no handle found from any strategy, return None
    if not handle:
        logger.error("All strategies failed to fetch user info. Cookies may be expired.")
        return None

    # ── Enrich: Scrape public profile for latest avatar ──
    logger.info(f"Enriching data via public page for @{handle}...")
    try:
        try:
            ua_instance = UserAgent()
            random_ua = ua_instance.random
        except Exception:
            random_ua = get_random_user_agent()

        headers_scrape = {
            "User-Agent": random_ua,
            "Referer": "https://www.tiktok.com/",
            "Accept-Language": "en-US,en;q=0.9",
        }
        url_scrape = f"https://www.tiktok.com/@{handle}"

        r_scrape = requests.get(url_scrape, headers=headers_scrape, timeout=10, proxies=proxies)

        if r_scrape.status_code == 200:
            html = r_scrape.text

            # Try UNIVERSAL_DATA (current layout 2025+)
            if "__UNIVERSAL_DATA_FOR_REHYDRATION__" in html:
                univ = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', html)
                if univ:
                    try:
                        u_data = json.loads(univ.group(1))
                        user_detail = u_data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {}).get("user", {})
                        new_avatar = user_detail.get('avatarLarger') or user_detail.get('avatarMedium')
                        new_nickname = user_detail.get('nickname')
                        new_unique_id = user_detail.get('uniqueId')
                        if new_avatar:
                            logger.info(f"Avatar updated via UNIVERSAL: {new_avatar[:50]}...")
                            avatar_url = new_avatar
                        if new_nickname:
                            display_name = new_nickname
                        if new_unique_id:
                            handle = new_unique_id
                    except Exception:
                        pass

            # Try SIGI_STATE (legacy layout)
            if not avatar_url or avatar_url == "":
                sigi = re.search(r'<script id="SIGI_STATE" type="application/json">(.+?)</script>', html)
                if sigi:
                    try:
                        data = json.loads(sigi.group(1))
                        user_module = data.get("UserModule", {}).get("users", {})
                        user_info = user_module.get(handle)
                        if not user_info:
                            for k, v in user_module.items():
                                if v.get("uniqueId") == handle:
                                    user_info = v
                                    break
                        if user_info:
                            new_avatar = user_info.get('avatarLarger') or user_info.get('avatarMedium')
                            if new_avatar:
                                avatar_url = new_avatar
                    except Exception:
                        pass

    except Exception as e:
        logger.warning(f"Public page scrape failed (using API data): {e}")

    return {
        "display_name": display_name or handle,
        "username": handle,
        "avatar_url": avatar_url or ""
    }

def enrich_session_metadata(session_path):
    """
    Verifica se a sessão tem metadados enriquecidos. Se não, busca e atualiza.
    """
    data = load_session_data(session_path)
    if not data:
        return None
        
    # Verifica cache (TTL de 24h?)
    meta = data.get("synapse_meta", {})
    last_checked = meta.get("last_checked", 0)
    now = time.time()
    
    # Se já tem dados e tem menos de 1 hora, retorna cache
    if meta.get("display_name") and (now - last_checked < 3600):
        return meta

    # Busca novo
    logger.info(f"🔄 Atualizando metadados para {os.path.basename(session_path)}...")
    cookies = extract_cookies_dict(data)
    if cookies:
        info = fetch_tiktok_user_info(cookies)
        if info:
            meta.update(info)
            meta["last_checked"] = now
            data["synapse_meta"] = meta
            save_session_data(session_path, data)
            logger.info(f"✅ Metadados atualizados: {info['display_name']}")
            return meta
            
    return meta # Retorna o que tinha (ou vazio)
