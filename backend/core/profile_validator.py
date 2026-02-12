import asyncio
import logging
import os # Added import
from typing import Dict, Optional
from core.session_manager import get_session_path, update_profile_info, update_profile_metadata, update_profile_status, get_profile_metadata, get_profile_user_agent

logger = logging.getLogger(__name__)


async def validate_profile(profile_id: str, headless: bool = True) -> Dict:
    """
    Launches browser with profile cookies, navigates to TikTok,
    extracts avatar and nickname using Context JSON, and updates the profile metadata.
    """
    logger.info(f"🕵️ Validating profile: {profile_id} (Headless: {headless})")
    
    session_path = get_session_path(profile_id)
    
    # NEW: Persistent Context Logic
    # We check if a context dir exists. If so, we use it.
    from core.session_manager import get_context_path
    context_path = get_context_path(profile_id)
    use_persistent = os.path.exists(context_path)
    
    p = None
    browser = None
    
    try:
        # Launch headless browser with stealth
        from core.browser import launch_browser, close_browser
        from core.network_utils import get_random_user_agent, DEFAULT_UA
        
        # [SYN-FIX] FORCE Desktop UA for validation. The tiktokstudio/upload route
        # is a DESKTOP-ONLY feature. Using a Mobile UA (like iPhone) causes TikTok
        # to redirect to the App Store (onelink.me), which breaks the session check.
        # The stored profile UA is preserved for other operations, but validation MUST use Desktop.
        user_agent = DEFAULT_UA
        
        launch_kwargs = {
            "headless": headless,
            "user_agent": user_agent
        }
        
        if use_persistent:
            launch_kwargs["user_data_dir"] = context_path
            # When using persistent context, cookies are loaded from the dir automatically.
            # We don't necessarily need storage_state, but we can update it later.
            logger.info(f"Using Persistent Context at {context_path}")
        else:
            launch_kwargs["storage_state"] = session_path
            
        p, browser, context, page = await launch_browser(**launch_kwargs)
        
        # Navigate to TikTok Studio upload page
        # This page contains the __Creator_Center_Context__ with full user info
        from core.network_utils import get_upload_url
        logger.info(f"Navigating to TikTok Studio for profile: {profile_id}")
        
        # 🔄 [SYN-FIX] Retry navigation if it fails/crashes
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                await page.goto(get_upload_url(), timeout=60000, wait_until="domcontentloaded")
                break
            except Exception as e:
                if attempt == max_retries:
                    raise e
                logger.warning(f"Navigation attempt {attempt+1} failed ({e}), retrying {attempt+2}/{max_retries+1}...")
                await asyncio.sleep(2)
        
        # SECURITY CHECK: Detect Login Redirect (Dead Session/Limited Access)
        current_url = page.url
        if "login" in current_url or "tiktok.com" not in current_url:
            logger.error(f"SESSAO MORTA DETECTADA EM VALIDACAO! Redirecionado para login: {current_url}")
            # Mark as inactive immediately
            # update_profile_status(profile_id, False)
            raise Exception("Session Expired - Login Required")
        
        # [SYN-FIX] Check for Mobile -> App Store Redirect
        if "onelink.me" in current_url:
            logger.error(f"REDIRECIONAMENTO PARA APP STORE DETECTADO! URL: {current_url}")
            raise Exception("Session Expired - Mobile Redirect Detected")
        
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
                            unique_id: user.uniqueId,
                            bio: user.signature,
                            follower_count: user.followerCount,
                            following_count: user.followingCount
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
                "bio": profile_data.get("bio", ""),
                "oracle_best_times": [], # Preserve or Init? Currently init empty if not merging.
                # Actually update_profile_info merges specific keys.
                # using update_profile_metadata explicitly for everything? 
                # update_profile_info in session_manager handles specific keys: avatar_url, nickname, username.
                # We need to enhance session_manager too if we want to save bio.
                "validated_at": "now"
            }
            
            # We need to save bio/stats too. 
            # Passing them in result_data relies on update_profile_info handling them.
            # Let's check session_manager again. It handles 'nickname'->label, 'username', 'avatar_url'.
            # It ignores others.
            # We should call update_profile_metadata for the rest.
             
            update_success = update_profile_info(profile_id, result_data)
            
            update_profile_metadata(profile_id, {
                "bio": profile_data.get("bio", ""),
                "stats": {
                    "followers": profile_data.get("follower_count", 0),
                    "following": profile_data.get("following_count", 0)
                }
            })
            
            if update_success:
                # Reactivate profile since validation was successful
                update_profile_status(profile_id, True)
                
                # [SYN-FIX] Clear error state so frontend shows ATIVO not ERRO
                # Frontend getHealthStatus checks last_error_screenshot FIRST
                update_profile_metadata(profile_id, {"last_error_screenshot": None})
                
                logger.info("Profile updated and reactivated successfully!")
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

        # === NEW FALLBACK: Main Page Scraping (to find username) ===
        if not avatar_src:
            logger.info("Accessing Main Page to recover session/username...")
            try:
                await page.goto("https://www.tiktok.com/", timeout=30000, wait_until="networkidle")
                
                # Try to find profile link in header
                # Selectors for profile icon that links to @username
                header_profile_sel = '[data-e2e="profile-icon"]' 
                if await page.locator(header_profile_sel).count() > 0:
                    profile_link = await page.locator(header_profile_sel).xpath('..') # Parent <a>
                    if await profile_link.count() > 0:
                         href = await profile_link.first.get_attribute("href")
                         # href is usually /@username
                         if href and "/@" in href:
                             extracted_user = href.split("/@")[1].split("?")[0]
                             logger.info(f"Found username from header: {extracted_user}")
                             
                             # Update local metadata so public fallback can use it
                             update_profile_info(profile_id, {"username": extracted_user})
                             
                             # Also try to grab avatar here
                             avatar_src = await page.locator(header_profile_sel).first.get_attribute("src")
                
                # If still no avatar, check for generic avatar img in header
                if not avatar_src:
                     # fallback generic
                     pass
                     
            except Exception as e_main:
                logger.error(f"Main page recovery failed: {e_main}")

        if not avatar_src:
            # === PUBLIC FALLBACK ===
            logger.info("Attempting Public Profile Fallback (/@username)...")
            meta = get_profile_metadata(profile_id)
            username = meta.get("username")
            
            # If username was just recovered above, it should be in meta (reload it or use local var?)
            # update_profile_info writes to DB. get_profile_metadata reads from DB.
            # It might be cached or slow. Let's just pass it if we found it?
            # Actually, let's rely on DB or refetch.
            if not username:
                # Try one last check of the page URL if we are on a profile page
                if "/@" in page.url:
                    username = page.url.split("/@")[1].split("?")[0]

            if username:
                try:
                    await page.goto(f"https://www.tiktok.com/@{username}", timeout=30000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    
                    # Scrape Public Data
                    # Avatar
                    avatar_sel = 'img[class*="Avatar"], [data-e2e="user-avatar"] img'
                    if await page.locator(avatar_sel).count() > 0:
                        avatar_src = await page.locator(avatar_sel).first.get_attribute("src")
                    
                    # Stats
                    followers = 0
                    following = 0
                    likes = 0
                    bio = ""
                    
                    try:
                         # Selectors for 2024/2025 TikTok Layout
                         follower_el = await page.query_selector('[data-e2e="followers-count"]')
                         if follower_el:
                             followers = await follower_el.get_attribute("title") or await follower_el.inner_text()
                             
                         following_el = await page.query_selector('[data-e2e="following-count"]')
                         if following_el:
                             following = await following_el.get_attribute("title") or await following_el.inner_text()
                             
                         bio_el = await page.query_selector('[data-e2e="user-bio"]')
                         if bio_el:
                             bio = await bio_el.inner_text()
                             
                    except Exception as scrape_err:
                        logger.warning(f"Public scrape partial fail: {scrape_err}")

                    if avatar_src:
                         logger.info(f"Public Fallback Success for @{username}")
                         result_data = {
                            "avatar_url": avatar_src,
                            "nickname": meta.get("label", username), # Keep existing label/nick if public scraping fails to find nick
                            "username": username,
                            "bio": bio,
                            "validated_at": "now"
                        }
                         
                         update_profile_info(profile_id, result_data)
                         
                         # Parse '1.2M' -> 1200000 roughly if needed, or save string. Database expects int for stats usually?
                         # For now saving raw strings or simple integers if possible. 
                         # Let's clean it simply.
                         def parse_count(val):
                             if not val: return 0
                             if isinstance(val, int): return val
                             val = val.lower().replace("followers", "").strip()
                             multi = 1
                             if "m" in val: multi = 1000000; val=val.replace("m","")
                             elif "k" in val: multi = 1000; val=val.replace("k","")
                             try: return int(float(val) * multi)
                             except: return 0

                         update_profile_metadata(profile_id, {
                            "bio": bio,
                            "stats": {
                                "followers": parse_count(followers),
                                "following": parse_count(following)
                            }
                        })
                        
                         # Reactivate profile since validation was successful
                         update_profile_status(profile_id, True)
                         update_profile_metadata(profile_id, {"last_error_screenshot": None})
                         
                         return {
                            "status": "success",
                            "profile_id": profile_id, 
                            "avatar_url": avatar_src,
                            "message": "Profile validation successful (Public Fallback)"
                        }

                except Exception as pub_err:
                    logger.error(f"Public Fallback Failed: {pub_err}")

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
            # Reactivate profile since validation was successful
            update_profile_status(profile_id, True)
            update_profile_metadata(profile_id, {"last_error_screenshot": None})
            return {
                "status": "success",
                "profile_id": profile_id, 
                "avatar_url": avatar_src,
                "message": "Profile validation successful (CSS Fallback)"
            }
        
        return {"status": "error", "message": "Failed to update local db (CSS Fallback)"}

    except Exception as e:
        logger.error(f"Validation failed for {profile_id}: {e}")
        
        # Mark session as invalid in DB
        # update_profile_status(profile_id, False) # active=False
        
        # Capture Screenshot for Visual Debugging
        screenshot_url = None
        try:
            if page:
                screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "debug_screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                filename = f"{profile_id}_error.png"
                filepath = os.path.join(screenshots_dir, filename)
                await page.screenshot(path=filepath, full_page=False)
                # URL assuming /static mount
                screenshot_url = f"/static/debug_screenshots/{filename}?t={int(asyncio.get_event_loop().time())}"
                
                # Update metadata with screenshot
                update_profile_metadata(profile_id, {"last_error_screenshot": screenshot_url})
        except Exception as screen_err:
            logger.error(f"Failed to capture error screenshot: {screen_err}")

        import traceback
        traceback.print_exc()
        
        # Log to debug file (keeping existing log logic)
        try:
            with open("validator_debug.log", "a", encoding="utf-8") as f:
                f.write(f"ERROR {profile_id}: {str(e)}\n{traceback.format_exc()}\n")
        except: pass
        
        return {
            "status": "error",
            "profile_id": profile_id,
            "message": str(e),
            "error_screenshot": screenshot_url
        }
    finally:
        await close_browser(p, browser)

