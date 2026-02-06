import json
import os
import logging
import requests
import time
from datetime import datetime

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

def fetch_tiktok_user_info(cookies):
    """
    Busca informações do usuário.
    Estratégia Híbrida:
    1. Tenta raspar a página pública de perfil (mais preciso para avatar atual).
    2. Fallback para API Passport (mais estável, mas pode ter avatar antigo).
    """
    import re
    from core.network_utils import get_tiktok_headers, get_passport_api_url
    
    # Passo 1: Consulta Rápida no Passport para pegar o HANDLE correto
    headers_api = get_tiktok_headers()
    url_api = get_passport_api_url()
    
    passport_data = None
    try:
        r = requests.get(url_api, cookies=cookies, headers=headers_api, timeout=5)
        if r.status_code == 200:
            wrapper = r.json()
            passport_data = wrapper.get("data", {})
    except Exception as e:
        logger.warning(f"Passport API falhou: {e}")

    # Se falhou tudo, retorna None
    if not passport_data:
        return None

    # Dados base do Passport
    # NOTA: Na API Passport, 'username' é geralmente o unique_id (handle) e 'screen_name' é o Display Name.
    handle = passport_data.get("username", "")       # ex: opiniaoviral
    display_name = passport_data.get("screen_name", "") # ex: Guilherme Corrêa
    avatar_url = passport_data.get("avatar_url", "")
    
    if not handle:
         # Se não tem handle, retorna o que tem
         return {
             "display_name": display_name or handle, 
             "username": "unknown",
             "avatar_url": avatar_url
         }

    # Passo 2: Tentar Enriquecer com Scrape da Página Pública (para Avatar Atualizado)
    logger.info(f"Tentando enriquecer dados via página pública para @{handle}...")
    try:
        ua = UserAgent()
        headers_scrape = {
            "User-Agent": ua.random,
            "Referer": "https://www.tiktok.com/",
            "Accept-Language": "en-US,en;q=0.9",
        }
        url_scrape = f"https://www.tiktok.com/@{handle}"
        
        r2 = requests.get(url_scrape, headers=headers_scrape, cookies=cookies, timeout=10)
        
        if r2.status_code == 200:
            html = r2.text
            
            # Tenta SIGI_STATE
            sigi = re.search(r'<script id="SIGI_STATE" type="application/json">(.+?)</script>', html)
            if sigi:
                try:
                    data = json.loads(sigi.group(1))
                    user_module = data.get("UserModule", {}).get("users", {})
                    # Tenta pegar pelo handle (as vezes é lower case ou tem chaves diferentes)
                    user_info = user_module.get(handle)
                    if not user_info:
                        # Busca linear
                        for k, v in user_module.items():
                            if v.get("uniqueId") == handle:
                                user_info = v
                                break
                    
                    if user_info:
                        new_avatar = user_info.get('avatarLarger') or user_info.get('avatarMedium')
                        if new_avatar:
                            logger.info(f"Avatar atualizado via SIGI: {new_avatar[:30]}...")
                            avatar_url = new_avatar
                except:
                    pass

            # Tenta UNIVERSAL_DATA (Novo Layout 2024/2025)
            if "UNIVERSAL_DATA_FOR_REHYDRATION" in html:
                 univ = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', html)
                 if univ:
                     try:
                         u_data = json.loads(univ.group(1))
                         user_detail = u_data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {}).get("user", {})
                         new_avatar = user_detail.get('avatarLarger') or user_detail.get('avatarMedium')
                         if new_avatar:
                             logger.info(f"Avatar atualizado via UNIVERSAL: {new_avatar[:30]}...")
                             avatar_url = new_avatar
                     except:
                         pass

    except Exception as e:
        logger.warning(f"Falha no scrape público (usando fallback passport): {e}")

    return {
        "display_name": display_name, 
        "username": handle,       
        "avatar_url": avatar_url  
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
