import logging
import os
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


def is_production() -> bool:
    """Checks if we are running in a production environment."""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


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


def get_profile_identity(profile_slug: str) -> Dict[str, Any]:
    """
    Resolves the complete browser identity for a profile from the database.
    
    Returns a dict with:
        - proxy: Dict with server/username/password or None
        - user_agent: str
        - viewport: Dict with width/height
        - locale: str
        - timezone: str
        - geolocation: Dict with latitude/longitude or None
        - has_proxy: bool
    
    In PRODUCTION, raises MissingProxyError if no proxy is configured.
    In DEVELOPMENT, logs a warning and returns defaults without proxy.
    """
    from core.retry_utils import MissingProxyError

    identity = {
        "proxy": None,
        "user_agent": DEFAULT_UA,
        "viewport": {"width": 1920, "height": 1080},
        "locale": DEFAULT_LOCALE,
        "timezone": DEFAULT_TIMEZONE,
        "geolocation": None,
        "has_proxy": False,
    }

    # Try database first
    try:
        from core.database import SessionLocal
        from core.models import Profile

        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(Profile.slug == profile_slug).first()
            if profile:
                # Proxy: check relationship first (modern), then legacy fields
                if profile.proxy:
                    identity["proxy"] = {
                        "server": profile.proxy.server,
                        "username": profile.proxy.username,
                        "password": profile.proxy.password,
                    }
                    identity["has_proxy"] = True
                    # If proxy has global fingerprint overrides, apply them
                    if profile.proxy.fingerprint_ua:
                        identity["user_agent"] = profile.proxy.fingerprint_ua
                    if profile.proxy.geolocation_latitude and profile.proxy.geolocation_longitude:
                        identity["geolocation"] = {
                            "latitude": float(profile.proxy.geolocation_latitude),
                            "longitude": float(profile.proxy.geolocation_longitude),
                        }
                elif profile.proxy_server:
                    identity["proxy"] = {
                        "server": profile.proxy_server,
                        "username": profile.proxy_username,
                        "password": profile.proxy_password,
                    }
                    identity["has_proxy"] = True

                # User-Agent (Profile override > Proxy > default)
                if profile.fingerprint_ua:
                    identity["user_agent"] = profile.fingerprint_ua

                # Viewport
                identity["viewport"] = {
                    "width": profile.fingerprint_viewport_w or 1920,
                    "height": profile.fingerprint_viewport_h or 1080,
                }

                # Locale & Timezone
                if profile.fingerprint_locale:
                    identity["locale"] = profile.fingerprint_locale
                if profile.fingerprint_timezone:
                    identity["timezone"] = profile.fingerprint_timezone

                # Geolocation (Profile override > Proxy)
                if profile.geolocation_latitude and profile.geolocation_longitude:
                    identity["geolocation"] = {
                        "latitude": float(profile.geolocation_latitude),
                        "longitude": float(profile.geolocation_longitude),
                    }
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"[IDENTITY] Erro ao resolver identidade do perfil '{profile_slug}' via DB: {e}")

    # Fallback: try session JSON for UA (legacy support)
    if identity["user_agent"] == DEFAULT_UA:
        try:
            from core.session_manager import get_profile_user_agent
            legacy_ua = get_profile_user_agent(profile_slug)
            if legacy_ua and legacy_ua != DEFAULT_UA:
                identity["user_agent"] = legacy_ua
        except Exception:
            pass

    # PRODUCTION HARD BLOCK: No proxy = abort
    if is_production() and not identity["has_proxy"]:
        raise MissingProxyError(profile_slug)

    # DEVELOPMENT WARNING
    if not identity["has_proxy"]:
        logger.warning(
            f"[IDENTITY] Perfil '{profile_slug}' SEM proxy configurado. "
            f"Em producao, isso sera um HARD BLOCK."
        )

    return identity

