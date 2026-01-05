"""
TikTok Uploader Module
Handles video upload to TikTok Studio using Playwright with session persistence.
"""
import asyncio
import os
import sys
import logging
from typing import Optional

# Add parent dir to path for imports when running as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import Page
from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path

logger = logging.getLogger(__name__)

async def upload_video(
    session_name: str,
    video_path: str,
    caption: str,
    hashtags: list = None,
    schedule_time: str = None, # Format: "YYYY-MM-DD HH:MM"
    post: bool = False
) -> dict:
    """
    Uploads a video to TikTok Studio.
    
    Args:
        session_name: Name of the session file (without .json)
        video_path: Absolute path to the video file
        caption: Caption text for the video
        hashtags: List of hashtags (without #)
        post: If True, actually clicks the Post button. Default False for safety.
        
    Returns:
        dict with status, message, and screenshot_path
    """
    result = {
        "status": "error",
        "message": "",
        "screenshot_path": None
    }
    
    # Validate video file exists
    if not os.path.exists(video_path):
        result["message"] = f"Video file not found: {video_path}"
        logger.error(result["message"])
        return result
    
    # Load session
    session_path = get_session_path(session_name)
    if not os.path.exists(session_path):
        result["message"] = f"Session not found: {session_path}"
        logger.error(result["message"])
        return result
    
    logger.info(f"Starting upload: {video_path}")
    logger.info(f"Caption: {caption}")
    
    p = None
    browser = None
    
    try:
        # Launch browser with session
        p, browser, context, page = await launch_browser(
            headless=False,
            storage_state=session_path
        )
        
        # Navigate to TikTok Studio Upload
        upload_url = "https://www.tiktok.com/tiktokstudio/upload"
        logger.info(f"Navigating to {upload_url}")
        await page.goto(upload_url, timeout=120000, wait_until="load")
        await page.wait_for_timeout(5000)  # Initial load wait
        
        # Find the hidden file input
        # TikTok Studio uses a hidden input that gets triggered by clicking the upload area
        logger.info("Looking for file input or upload trigger...")
        
        file_input = None
        
        # Method 1: Try to find visible file input directly
        try:
            file_input = await page.wait_for_selector('input[type="file"]', timeout=10000, state="attached")
            logger.info("Found file input element")
        except:
            logger.info("No visible file input, trying alternative approach...")
        
        if file_input:
            # Upload the video file
            logger.info(f"Uploading file: {video_path}")
            await file_input.set_input_files(video_path)
        else:
            # Method 2: Use file chooser approach - click upload area and handle dialog
            logger.info("Using file chooser approach...")
            try:
                # Look for the upload button/area and use file chooser
                upload_selectors = [
                    'button:has-text("Select file")',
                    'button:has-text("Select video")',
                    '[class*="upload"]',
                    '[data-testid*="upload"]',
                    'div:has-text("Select video to upload")',
                    'div:has-text("Select file")',
                ]
                
                for selector in upload_selectors:
                    try:
                        upload_trigger = await page.wait_for_selector(selector, timeout=3000)
                        if upload_trigger:
                            # Handle file chooser dialog
                            async with page.expect_file_chooser() as fc_info:
                                await upload_trigger.click()
                            file_chooser = await fc_info.value
                            await file_chooser.set_files(video_path)
                            logger.info(f"File uploaded via file chooser: {selector}")
                            break
                    except Exception as e:
                        continue
                else:
                    # Method 3: Brute force - click center of page and try file chooser
                    logger.info("Trying click on page center...")
                    try:
                        async with page.expect_file_chooser(timeout=5000) as fc_info:
                            await page.mouse.click(500, 300)
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(video_path)
                        logger.info("File uploaded via center click")
                    except:
                        result["message"] = "Could not trigger file upload"
                        logger.error(result["message"])
                        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
                        await page.screenshot(path=os.path.join(static_dir, "upload_error.png"), full_page=True)
                        return result
            except Exception as e:
                result["message"] = f"File upload failed: {e}"
                logger.error(result["message"])
                static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
                await page.screenshot(path=os.path.join(static_dir, "upload_error.png"), full_page=True)
                return result
        
        # Wait for upload to complete (monitor progress or specific element)
        logger.info("Waiting for upload to complete...")
        await page.wait_for_timeout(5000)  # Initial wait (reduced from 10s)
        
        # Try to detect upload completion
        try:
            await page.wait_for_selector('text=Post', timeout=60000)
            logger.info("Upload appears complete (Post button visible)")
        except:
            logger.warning("Could not confirm upload completion, proceeding anyway...")
        
        # ========== JAVASCRIPT INJECTION ANTI-POPUP ==========
        logger.info("💉 Injetando 'Vacina Anti-Popup' via JavaScript...")
        
        # Build full caption with hashtags
        full_caption = caption
        if hashtags:
            full_caption += " " + " ".join([f"#{h}" for h in hashtags])
        
        # 1. Injeta um script que fica clicando no botão "Entendi" a cada 100ms
        # Seletor descoberto pelo usuário: [data-e2e="tutorial-tooltip-got-it-btn"]
        await page.evaluate("""
            // Anti-Popup Vaccine - Runs every 100ms
            if (!window.__antiPopupInjected) {
                window.__antiPopupInjected = true;
                setInterval(() => {
                    // Lista de seletores de popup para matar
                    const selectors = [
                        '[data-e2e="tutorial-tooltip-got-it-btn"]',
                        '[data-e2e="guide-got-it"]',
                        'button:contains("Entendi")',
                        'button:contains("Got it")',
                    ];
                    
                    selectors.forEach(sel => {
                        try {
                            const btn = document.querySelector(sel);
                            if (btn && btn.offsetParent !== null) {
                                console.log('💥 Popup detectado pelo JS! Destruindo:', sel);
                                btn.click();
                            }
                        } catch(e) {}
                    });
                }, 100);
                console.log('💉 Anti-Popup Vaccine INJECTED!');
            }
        """)
        
        logger.info("✅ Vacina injetada! Aguardando 1s para ela agir...")
        await page.wait_for_timeout(1000)
        
        # 2. Agora o Python só foca na legenda
        logger.info("📝 Tentando preencher legenda...")
        caption_filled = False
        
        try:
            # Espera a legenda ficar clicável (o JS vai matar o popup se ele aparecer na frente)
            await page.locator('.public-DraftEditor-content').click(timeout=10000)
            
            # Limpa e Escreve
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(full_caption, delay=50)
            
            logger.info("✅ Legenda Preenchida!")
            caption_filled = True
        except Exception as e:
            logger.error(f"❌ Erro ao preencher legenda: {e}")
        
        await page.wait_for_timeout(1500)
        # ========== END JAVASCRIPT INJECTION ==========
        
        # Take proof screenshot (before posting)
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        screenshot_path = os.path.join(static_dir, "upload_fixed.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"Screenshot saved: {screenshot_path}")
        
        result["screenshot_path"] = screenshot_path
        
        # ========== SCHEDULING & POST LOGIC ==========
        
        target_button_text = "Publicar" # Default
        
        if schedule_time:
            logger.info(f"⏳ Agendamento solicitado para: {schedule_time}")
            try:
                # 1. Ativar modo Agendamento
                # Procura pelo texto "Programar vídeo" ou toggle similar
                schedule_toggle = page.locator('div').filter(has_text="Programar vídeo").last
                if not await schedule_toggle.is_visible():
                     schedule_toggle = page.locator('text=Programar vídeo')
                
                # Clica no toggle/radio
                # Muitas vezes o input está escondido e o clique é no label/div
                await schedule_toggle.click()
                logger.info("✅ Toggle 'Programar vídeo' clicado")
                await page.wait_for_timeout(1000)
                
                # 2. Preencher Data e Hora
                # O TikTok revela dois inputs. Vamos tentar achá-los.
                # Geralmente inputs de data/hora
                
                from datetime import datetime
                dt = datetime.fromisoformat(schedule_time)
                
                # Formatações prováveis (TikTok varia por região, mas ISO costuma funcionar em inputs modernos)
                date_str = dt.strftime('%Y-%m-%d') # AAAA-MM-DD
                time_str = dt.strftime('%H:%M')    # HH:MM
                
                # Tenta preencher inputs visíveis de data/hora
                # Input de Data
                date_input = page.locator('.jp-date-picker input, input[placeholder*="YYYY"], input[placeholder*="AAAA"]').first
                if await date_input.is_visible():
                    await date_input.click()
                    await date_input.fill(date_str)
                    await page.keyboard.press("Enter")
                    logger.info(f"📅 Data preenchida: {date_str}")
                else:
                    logger.warning("⚠️ Input de data não encontrado com seletores padrão.")

                # Input de Hora
                time_input = page.locator('.jp-time-picker input, input[placeholder*="HH:MM"]').first
                if await time_input.is_visible():
                    await time_input.click()
                    await time_input.fill(time_str)
                    await page.keyboard.press("Enter")
                    logger.info(f"⏰ Hora preenchida: {time_str}")
                else:
                     logger.warning("⚠️ Input de hora não encontrado.")
                
                target_button_text = "Programar"
                
            except Exception as e:
                logger.error(f"❌ Erro na lógica de agendamento: {e}")
                # Fallback: Tenta postar normal ou aborta?
                # Vamos manter Publicar se falhar o agendamento? Melhor não, perigoso.
                # target_button_text = "Publicar" 
        
        # 3. Finalizar (Clicar no Botão de Ação)
        if post or schedule_time: # Se for agendamento, SEMPRE executa o clique final (pois é o objetivo)
            logger.info(f"🚀 Executando ação final: {target_button_text}...")
            try:
                # Procura botão com o texto exato
                action_button = page.locator(f'button:has-text("{target_button_text}")').first
                
                # Fallback para botão de "Post" genérico se for Publicar
                if not await action_button.is_visible() and target_button_text == "Publicar":
                     action_button = page.locator('button:has-text("Post")').first
                
                if await action_button.is_visible():
                    await action_button.click()
                    logger.info(f"✅ Botão '{target_button_text}' clicado com sucesso!")
                    
                    # Espera a confirmação (modal de sucesso ou navegação)
                    await page.wait_for_timeout(5000)
                    
                    result["status"] = "posted" if not schedule_time else "scheduled"
                    result["message"] = f"Video processed successfully ({target_button_text})"
                else:
                    logger.error(f"❌ Botão '{target_button_text}' não encontrado!")
                    result["message"] = f"Button '{target_button_text}' not found"
                    
            except Exception as e:
                result["message"] = f"Failed to click action button: {e}"
                logger.error(result["message"])
        else:
            result["status"] = "ready"
            result["message"] = "Upload ready (Manual Action Required)"
            logger.info("⏸️ Post/Schedule desativado. Aguardando ação manual.")
            
        # ========== END SCHEDULING & POST LOGIC ==========
        
    except Exception as e:
        result["message"] = f"Upload failed: {str(e)}"
        logger.error(result["message"])
        import traceback
        traceback.print_exc()
        
    finally:
        logger.info("Closing browser...")
        if p and browser:
            await close_browser(p, browser)
            
    return result


# CLI Entry Point
if __name__ == "__main__":
    import sys
    
    # Default test values
    SESSION_NAME = "tiktok_profile_01"
    VIDEO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "teste.mp4")
    CAPTION = "Teste Synapse Automático V2 🚀"
    HASHTAGS = ["fy"]
    
    print(f"=== TIKTOK UPLOADER TEST ===")
    print(f"Session: {SESSION_NAME}")
    print(f"Video: {VIDEO_PATH}")
    print(f"Caption: {CAPTION} #{' #'.join(HASHTAGS)}")
    print(f"POST MODE: DISABLED (safety)")
    print("="*30)
    
    result = asyncio.run(upload_video(
        session_name=SESSION_NAME,
        video_path=VIDEO_PATH,
        caption=CAPTION,
        hashtags=HASHTAGS,
        post=False  # NEVER auto-post in test mode
    ))
    
    print(f"\nResult: {result}")
