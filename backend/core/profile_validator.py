import asyncio
import logging
from typing import Dict, Optional
from core.session_manager import get_session_path, update_profile_info

logger = logging.getLogger(__name__)


async def validate_profile(profile_id: str) -> Dict:
    """
    Launches browser with profile cookies, navigates to TikTok,
    extracts avatar and nickname using Context JSON, and updates the profile metadata.
    """
    logger.info(f"🕵️ Validating profile: {profile_id}")
    
    session_path = get_session_path(profile_id)
    p = None
    browser = None
    
    try:
        # Launch headless browser with stealth
        from core.browser import launch_browser, close_browser
        
        p, browser, context, page = await launch_browser(
            headless=True, 
            storage_state=session_path
        )
        
        # Navigate to TikTok Studio upload page
        # This page contains the __Creator_Center_Context__ with full user info
        logger.info(f"Navigating to TikTok Studio for profile: {profile_id}")
        await page.goto("https://www.tiktok.com/upload?lang=en", timeout=60000, wait_until="domcontentloaded")
        
        # Wait for the page to reach a stable state where the context script is likely present
        try:
            await page.wait_for_selector("#__Creator_Center_Context__", timeout=15000, state="attached")
        except:
            logger.warning("Context script selector timed out, likely not logged in or different layout.")

        # Attempt to extract profile data from the __Creator_Center_Context__ script tag
        profile_data = await page.evaluate('''() => {
            const contextScript = document.getElementById('__Creator_Center_Context__');
            if (contextScript) {
                try {
                    let rawContent = contextScript.textContent;
                    // Decode HTML entities if present (e.g. &quot;)
                    if (rawContent.includes('&quot;')) {
                        const txt = document.createElement("textarea");
                        txt.innerHTML = rawContent;
                        rawContent = txt.value;
                    }
                    
                    const data = JSON.parse(rawContent);
                    const user = data.commonAppContext?.user;
                    if (user) {
                        return {
                            avatar_url: user.avatarUri?.[0], // Get first avatar URL
                            nickname: user.nickName,
                            unique_id: user.uniqueId
                        };
                    }
                } catch (e) {
                    return { error: e.toString(), raw: contextScript.textContent.substring(0, 100) };
                }
            }
            return null;
        }''')

        if profile_data and profile_data.get("avatar_url"):
            logger.info(f"Successfully extracted profile data via Context JSON: {profile_data['nickname']}")
            
            result_data = {
                "avatar_url": profile_data["avatar_url"],
                "nickname": profile_data["nickname"],
                "username": profile_data["unique_id"],
                "validated_at": "now"
            }
            
            update_success = update_profile_info(profile_id, result_data)
            
            if update_success:
                logger.info("✅ Profile updated successfully!")
                return {
                    "status": "success",
                    "profile_id": profile_id,
                    "avatar_url": profile_data["avatar_url"],
                    "nickname": profile_data["nickname"],
                    "username": profile_data["unique_id"],
                    "message": "Profile validation successful (Context JSON)"
                }
            else:
                return {"status": "error", "message": "Failed to update local db"}

        # Fallback to visual selectors if JSON extraction fails
        logger.info("Context JSON extraction failed, falling back to CSS selectors...")
        
        potential_selectors = [
            "img[class*='Avatar']", 
            "img[class*='avatar']",
            "header img",
            "div[class*='avatar-container'] img"
        ]
        
        avatar_src = None
        for selector in potential_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=2000)
                if element:
                    avatar_src = await element.get_attribute("src")
                    if avatar_src:
                        break
            except:
                continue
                
        if not avatar_src:
             # Final check for background image
             try:
                 div_element = await page.query_selector("div[class*='Avatar']")
                 if div_element:
                     style = await div_element.get_attribute("style")
                     if style and "background-image" in style:
                         import re
                         match = re.search(r'url\("?(.+?)"?\)', style)
                         if match:
                             avatar_src = match.group(1)
             except:
                 pass

        if not avatar_src:
            raise Exception("Could not find avatar image. Session might be invalid or expired.")
            
        logger.info(f"Validator found avatar URL via CSS: {avatar_src}")
        
        # If we only got avatar via CSS, we might not have nickname
        result_data = {
            "avatar_url": avatar_src,
            "validated_at": "now"
        }
        
        update_success = update_profile_info(profile_id, result_data)
        
        if update_success:
            return {
                "status": "success",
                "profile_id": profile_id, 
                "avatar_url": avatar_src,
                "message": "Profile validation successful (CSS Fallback)"
            }
        
        return {"status": "error", "message": "Failed to update local db (CSS Fallback)"}

    except Exception as e:
        logger.error(f"Validation failed for {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "profile_id": profile_id,
            "message": str(e)
        }
    finally:
        await close_browser(p, browser)

