from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from fake_useragent import UserAgent
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ValidateCookiesRequest(BaseModel):
    cookies: str

class ValidateCookiesResponse(BaseModel):
    valid: bool
    username: str | None = None
    avatar_url: str | None = None
    error: str | None = None
    
@router.post("/validate-cookies", response_model=ValidateCookiesResponse)
async def validate_cookies(request: ValidateCookiesRequest):
    """
    Validates cookies by making a request to TikTok and extracting metadata.
    """
    try:
        cookies_list = json.loads(request.cookies)
    except json.JSONDecodeError:
        return ValidateCookiesResponse(valid=False, error="Invalid JSON format")
        
    try:
        # Prepare Session
        s = requests.Session()
        ua = UserAgent()
        headers = {
            "User-Agent": ua.random,
            "Referer": "https://www.tiktok.com/",
            "Origin": "https://www.tiktok.com"
        }
        
        # Set cookies
        for c in cookies_list:
            if isinstance(c, dict) and "name" in c and "value" in c:
                s.cookies.set(c["name"], c["value"], domain=c.get("domain", ".tiktok.com"))
        
        # Request Account Info (passport API)
        # NOTE: This returns the passport/account avatar, NOT the public profile avatar.
        # The public profile avatar is fetched separately by clicking "Refresh" 
        # which runs the full profile_validator with browser scraping.
        url = "https://www.tiktok.com/passport/web/account/info/"
        response = s.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
             return ValidateCookiesResponse(valid=False, error=f"TikTok API Error: {response.status_code}")
             
        data = response.json()
        if "data" in data and "username" in data["data"]:
            user_data = data["data"]
            return ValidateCookiesResponse(
                valid=True,
                username=user_data.get("username"),
                # This avatar is from passport (account), not public profile.
                # User should click Refresh to get the correct public avatar.
                avatar_url=user_data.get("avatar_url")
            )
        else:
             return ValidateCookiesResponse(valid=False, error="Session invalid or expired (No user data found)")
             
    except Exception as e:
        logger.error(f"Cookie validation error: {e}")
        return ValidateCookiesResponse(valid=False, error=str(e))
