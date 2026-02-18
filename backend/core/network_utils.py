import logging
import random
from typing import Dict, Any, Optional
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

# Instância única para evitar recriar toda vez
try:
    ua = UserAgent()
except Exception as e:
    logger.warning(f"Falha ao carregar UserAgent fake, usando fallback fixo: {e}")
    ua = None

# FIXED USER AGENT TO MATCH HEALED SESSIONS (Windows Desktop)
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
DEFAULT_LOCALE = "pt-BR"
DEFAULT_TIMEZONE = "America/Sao_Paulo"

# --- CONSTANTES DE URL ---
TIKTOK_BASE_URL = "https://www.tiktok.com"
TIKTOK_UPLOAD_URL = f"{TIKTOK_BASE_URL}/tiktokstudio/upload"
TIKTOK_CREATIVE_CENTER_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en"

def get_random_user_agent() -> str:
    """
    Retorna User-Agent fixo para garantir consistência com cookies de sessão.
    Evita rotação que causa 'Session Expired' por mismatch.
    """
    return DEFAULT_UA

def get_tiktok_headers(
    referer: str = "https://www.tiktok.com/",
    with_content_type: bool = False,
    extra_headers: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Retorna os headers padrão necessários para requisições ao TikTok (API/Fetch).
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Referer": referer,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.tiktok.com",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }
    
    if with_content_type:
        headers["Content-Type"] = "application/json; charset=UTF-8"
        
    if extra_headers:
        headers.update(extra_headers)
        
    return headers

def get_scrape_headers(user_agent: str = None) -> Dict[str, str]:
    """
    Headers otimizados para scraping de páginas públicas (Simula navegação real).
    """
    headers = {
        "User-Agent": user_agent or get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    return headers

def get_passport_api_url(aid: int = 1459, lang: str = "pt-BR") -> str:
    """Retorna a URL base para a API de info de conta (Passport)."""
    return f"https://www.tiktok.com/passport/web/account/info/?aid={aid}&app_language={lang}&app_name=tiktok_web"

def get_creative_center_url() -> str:
    """Retorna a URL do Creative Center do TikTok."""
    return TIKTOK_CREATIVE_CENTER_URL

def get_upload_url() -> str:
    """Retorna a URL de upload do TikTok Studio."""
    return TIKTOK_UPLOAD_URL
