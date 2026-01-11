"""
TikTok Uploader Module (Production)
Refactored: DOM NUKER V2 + Robust Scheduling + Modal Confirmation Fix
"""
import asyncio
import re
import os
import sys
import logging
from datetime import datetime

# Add parent dir to path
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
    schedule_time: str = None, 
    post: bool = False,
    viral_music_enabled: bool = False
) -> dict:
    result = {"status": "error", "message": "", "screenshot_path": None}
    
    if not os.path.exists(video_path):
        return {"status": "error", "message": "Video not found"}
    
    session_path = get_session_path(session_name)
    p, browser, context, page = await launch_browser(headless=False, storage_state=session_path)
    
    try:
        # STEP 1: Navegação
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=120000)
        await page.wait_for_timeout(5000)
        
        # Upload
        file_input = await page.wait_for_selector('input[type="file"]', timeout=30000, state="attached")
        await file_input.set_input_files(video_path)
        logger.info("Upload iniciado...")
        
        # ========== DOM NUKER V2 (CIRÚRGICO) ==========
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1000)
        await page.evaluate("""() => {
            const tutorialLocators = [
                '#react-joyride-portal', '.react-joyride__overlay', '[class*="TutorialTooltip"]',
                '[class*="GuideTooltip"]', '[data-e2e="tutorial-tooltip-got-it-btn"]',
                '[data-e2e*="got-it"]', 'button:has-text("Entendi")', 'button:has-text("Got it")'
            ];
            tutorialLocators.forEach(sel => {
                try {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                } catch(e) {}
            });
            // Click any "Got it" buttons that might be hidden
            Array.from(document.querySelectorAll('button')).forEach(btn => {
                const t = btn.innerText.toLowerCase();
                if (t.includes('entendi') || t.includes('got it') || t.includes('próximo')) btn.click();
            });
        }""")
        
        # ========== LEGENDA ==========
        full_caption = f"{caption} " + " ".join([f"#{h}" for h in hashtags]) if hashtags else caption
        editor = page.locator('.public-DraftEditor-content')
        await editor.wait_for(state="visible", timeout=30000)
        await editor.focus()
        await editor.press("Control+A")
        await editor.press("Backspace")
        await page.keyboard.type(full_caption, delay=50)
        
        # Espera upload concluir (pode demorar)
        logger.info("Aguardando upload concluir...")
        await page.wait_for_selector('text="Substituir", [data-e2e="upload-publish-btn"]:not([disabled])', timeout=180000)
        
        # ========== VIRAL AUDIO BOOST ==========
        if viral_music_enabled:
            logger.info("🎵 Iniciando Viral Audio Boost...")
            try:
                # 1. Clicar em Editar
                edit_btn = page.locator('button:has-text("Editar vídeo"), button:has-text("Edit video")').first
                if await edit_btn.is_visible():
                    await edit_btn.click()
                    await page.wait_for_timeout(5000) # Espera editor carregar
                    
                    # 2. Clicar em Música/Sons (Tentativa)
                    # Nota: Seletores aproximados baseados na UI padrão
                    music_tab = page.locator('div[role="tab"], button').filter(has_text=re.compile(r"Música|Music|Sound|Som", re.I)).first
                    if await music_tab.is_visible():
                        await music_tab.click()
                        await page.wait_for_timeout(2000)
                        
                        # 3. Selecionar Top 1 Global/Recomendado
                        # Geralmente a primeira lista é Trending
                        first_song = page.locator('.music-item, [class*="music-card"]').first
                        if await first_song.is_visible():
                            await first_song.hover()
                            use_btn = first_song.locator('button')
                            if await use_btn.count() > 0:
                                await use_btn.first.click()
                                logger.info("🎵 Música Viral aplicada!")
                                await page.wait_for_timeout(1000)
                                
                                    # 4. Ajustar Volume (CRÍTICO: Original 100%, Adicionado 0%)
                                    volume_tab = page.locator('div, button').filter(has_text=re.compile(r"Volume", re.I)).last
                                    if await volume_tab.is_visible():
                                        await volume_tab.click()
                                        await page.wait_for_timeout(500)
                                        
                                        # Tenta identificar sliders
                                        sliders = page.locator('input[type="range"]')
                                        count = await sliders.count()
                                        
                                        if count >= 2:
                                            # Geralmente: [0] = Original Sound, [1] = Added Sound
                                            # Vamos garantir: Original -> 100, Added -> 0
                                            
                                            # Set Original Sound to 100%
                                            await sliders.nth(0).fill("100")
                                            
                                            # Set Added Sound to 0% (CRITICAL)
                                            await sliders.nth(1).fill("0")
                                            
                                            logger.info("🔈 Volumes ajustados: Original=100%, Viral=0%")
                                        elif count == 1:
                                            # Se só tem um, assume que é o adicionado (se o original não for editável)
                                            await sliders.first.fill("0")
                                            logger.warning("⚠️ Apenas 1 slider encontrado. Definido para 0 (Assumindo ser música adicionada).")
                            
                    # 5. Salvar
                    save_edit = page.locator('button:has-text("Salvar edição"), button:has-text("Save edit"), button:has-text("Confirmar")').last
                    if await save_edit.is_visible():
                        await save_edit.click()
                        await page.wait_for_timeout(5000) # Espera processar
                        logger.info("✅ Edição salva.")
                    else:
                         logger.warning("Botão Salvar não encontrado, voltando...")
                         await page.keyboard.press("Escape")

                else:
                    logger.warning("Botão de Editar Vídeo não encontrado. Pulando Viral Boost.")

            except Exception as e:
                logger.error(f"❌ Falha no Viral Boost: {e}")
                # Tenta recuperar saindo do modal
                await page.keyboard.press("Escape")
        
        # ========== AGENDAMENTO ROBUSTO ==========
        if schedule_time:
            dt = datetime.fromisoformat(schedule_time)
            date_str = dt.strftime('%d/%m/%Y')
            target_time = dt.strftime('%H:%M')
            h_target, m_target = target_time.split(':')
            
            logger.info(f"⏳ Agendando para {date_str} às {target_time}")
            
            # 1. Ativando Switch
            toggle = page.locator('div, label, span').filter(has_text="Programar vídeo").last
            await toggle.click(force=True)
            await page.wait_for_timeout(1000)
            
            # 2. Data
            date_input = page.locator('.jp-date-picker input, input[placeholder*="DD/MM"]').first
            await date_input.click(force=True)
            await page.wait_for_timeout(500)
            # Tenta clicar no dia se possível ou digitar
            day = str(dt.day)
            day_el = page.locator(f'div[class*="day-item"], div[class*="calendar-day"]').filter(has_text=day).first
            if await day_el.is_visible():
                await day_el.click(force=True)
            else:
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await page.keyboard.type(date_str)
                await page.keyboard.press("Enter")
            
            # 3. Hora (Acurácia Visual Anchor)
            time_el = page.locator('.jp-time-picker input, [class*="time-picker-input"], [class*="tux-badge"]').first
            await time_el.click(force=True)
            await page.wait_for_timeout(1000)
            
            # Injeção JS Universal (Heurística de Listbox)
            await page.evaluate(f"""(parts) => {{
                const [h_val, m_val] = parts;
                const columns = Array.from(document.querySelectorAll('ul')).filter(u => u.querySelectorAll('li').length > 5);
                columns.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
                const setVal = (col, val) => {{
                    if (!col) return false;
                    const els = Array.from(col.querySelectorAll('li, span, div')).filter(e => e.innerText.trim() === val || parseInt(e.innerText) === parseInt(val));
                    if (els.length > 0) {{
                        els[0].scrollIntoView({{ block: "center" }});
                        els[0].click();
                        return true;
                    }}
                    return false;
                }};
                if (columns.length >= 2) {{ setVal(columns[0], h_val); setTimeout(() => setVal(columns[1], m_val), 500); }}
            }}""", [h_target, m_target])
            
            # Backup Teclado
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(target_time.replace(":", ""), delay=100)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(1000)
            await page.keyboard.press("Escape")

        # ========== CLIQUE FINAL & MODAL RETRY ==========
        btn_text = "Programar" if schedule_time else "Publicar"
        final_btn = page.locator(f'button:has-text("{btn_text}"), button:has-text("Agendar")').first
        
        if post:
            logger.info(f"🚀 Clicando em {btn_text}...")
            await final_btn.click(force=True)
            
            # LOOP DE CONFIRMAÇÃO DO MODAL
            for m_attempt in range(5):
                await page.wait_for_timeout(2500)
                # Procura por botões de confirmação em modais
                confirm_btn = page.locator('button:has-text("Programar"), button:has-text("Agendar"), button:has-text("Confirmar"), button:has-text("Publicar")').filter(has_not_text=btn_text).first
                if await confirm_btn.is_visible():
                    logger.info(f"📢 Modal de confirmação detectado. Confirmando...")
                    await confirm_btn.click(force=True)
                    await page.wait_for_timeout(3000)
                    break
                
                # Verifica se já saiu da página (sucesso)
                if page.url != "https://www.tiktok.com/tiktokstudio/upload":
                    logger.info("✅ Redirecionamento detectado! Postagem concluída.")
                    break
            
            result["status"] = "success"
            result["message"] = "Video posted/scheduled successfully"
        else:
            result["status"] = "ready"
            result["message"] = f"Ready to {btn_text}"
            
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        result["message"] = str(e)
    finally:
        await page.screenshot(path="backend/static/final_state.png")
        await close_browser(p, browser)
        
    return result
