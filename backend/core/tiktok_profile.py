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
    Busca informações do usuário na API do TikTok usando cookies.
    Retorna dict com username, display_name, avatar_url ou None se falhar.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.tiktok.com/",
    }
    url = "https://www.tiktok.com/passport/web/account/info/?aid=1459&app_language=pt-BR&app_name=tiktok_web"

    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            user_data = data.get("data", {})
            
            if user_data:
                # Prioridade: screen_name > username (depende da API, varia)
                # screen_name costuma ser o Display Name, username o @handle ou vice-versa no passport
                # Testes indicam: username = Display Name (ex: Cortes do João), screen_name = unique_id (com caracteres especiais?)
                # Vamos pegar ambos
                
                return {
                    "display_name": user_data.get("username", "Unknown"), 
                    "username": user_data.get("screen_name", "unknown"), # unique_id geralmente
                    "avatar_url": user_data.get("avatar_url", "")
                }
    except Exception as e:
        logger.error(f"Falha ao buscar info do TikTok: {e}")
        
    return None

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
