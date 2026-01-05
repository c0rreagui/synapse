import os
import time
import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright

# Configuração de Logs
logger = logging.getLogger("Uploader")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def handle_caption_and_popup(page, caption_text):
    """
    Vacina: Mata Popups e preenche a legenda.
    """
    logger.info("💉 Injetando 'Vacina Anti-Popup' via JavaScript...")
    
    await page.evaluate("""
        setInterval(() => {
            const selectors = [
                '[data-e2e="tutorial-tooltip-got-it-btn"]',
                '.react-joyride__overlay',
                '#react-joyride-portal',
                'button[aria-label="Close"]',
                'div[role="dialog"] button[aria-label="Fechar"]'
            ];
            selectors.forEach(s => {
                const el = document.querySelector(s);
                if (el) el.remove();
            });
        }, 500);
    """)
    
    logger.info("✅ Vacina ativa! Aguardando efeito...")
    await asyncio.sleep(1)

    logger.info("📝 Tentando preencher legenda...")
    try:
        # Foca no editor
        await page.locator('.public-DraftEditor-content').click(timeout=5000)
        # Limpa e escreve
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await page.keyboard.type(caption_text)
        logger.info("✅ Legenda Preenchida!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao preencher legenda: {e}")
        return False

async def upload_video(file_path, session_path, caption="Uploaded by Synapse", schedule_time=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(storage_state=session_path, no_viewport=True)
        page = await context.new_page()

        try:
            logger.info("🚀 Acessando TikTok Upload...")
            await page.goto("https://www.tiktok.com/tiktokstudio/upload")

            # --- CORREÇÃO 1: UPLOAD VIA INPUT DIRETO ---
            # Em vez de tentar clicar no botão visual, injetamos no input hidden
            logger.info(f"📤 Iniciando upload de: {os.path.basename(file_path)}")
            try:
                # O TikTok sempre tem um input type=file, mesmo que escondido
                await page.locator('input[type="file"]').set_input_files(file_path)
            except:
                # Fallback: Tenta clicar no texto "Selecionar arquivo" se o input falhar
                logger.warning("⚠️ Input direto falhou, tentando clique visual...")
                await page.locator("text=Selecionar arquivo").click()
                async with page.expect_file_chooser() as fc_info:
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(file_path)

            # Espera o upload processar (barra de carregamento ou editor aparecer)
            # MONITORIA DE UPLOAD: Espera "Enviando" sumir
            try:
                logger.info("⏳ Aguardando upload concluir (Enviando...)...")
                # Espera qualquer indicador de upload sumir (ajuste o seletor conforme necessidade)
                # O texto "Enviando" ou barra de progresso geralmente somem quando vai pro editor
                await page.locator("text=Enviando").wait_for(state="detached", timeout=300000)
                await page.locator("text=Uploading").wait_for(state="detached", timeout=300000)
                logger.info("✅ Upload concluído visualmente.")
            except:
                logger.warning("⚠️ Aviso: Indicador de upload não sumiu ou não foi encontrado. Prosseguindo...")

            # Garante que o editor está visível
            await page.wait_for_selector('.public-DraftEditor-content', state="visible", timeout=120000)
            
            # Popups e Legenda
            await handle_caption_and_popup(page, caption)

            # Scroll para ver o rodapé
            logger.info("📜 Rolando página...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            target_button_text = "Publicar"

            # --- CORREÇÃO 2: AGENDAMENTO VIA TAB ---
            if schedule_time:
                dt_obj = datetime.fromisoformat(schedule_time)
                date_str = dt_obj.strftime("%d/%m/%Y")
                time_str = dt_obj.strftime("%H:%M")
                
                logger.info(f"⏳ Modo Agendamento: {date_str} às {time_str}")
                
                # Procura o Toggle
                schedule_found = False
                toggle_selectors = ['.tiktok-switch', 'input[type="checkbox"][class*="schedule"]', 'label:has-text("Programar")']
                
                for sel in toggle_selectors:
                    if await page.locator(sel).first.is_visible():
                        logger.info(f"🔍 Ativando agendamento via: {sel}")
                        await page.locator(sel).first.click()
                        schedule_found = True
                        break
                
                if not schedule_found:
                    raise Exception("❌ Botão de agendamento não encontrado!")

                # ESTRATÉGIA TAB (Teclado)
                logger.info("⌨️ Navegando via TAB para preencher data...")
                await asyncio.sleep(2) # Espera animação
                
                try:
                    # Foca no Toggle de novo para garantir ponto de partida
                    await page.keyboard.press("Tab") # Vai para Data
                    await asyncio.sleep(0.5)
                    
                    # Preenche Data
                    await page.keyboard.press("Control+A")
                    await page.keyboard.type(date_str)
                    await page.keyboard.press("Enter")
                    logger.info(f"✅ Data digitada: {date_str}")
                    
                    await page.keyboard.press("Tab") # Vai para Hora
                    await asyncio.sleep(0.5)
                    
                    # Preenche Hora
                    await page.keyboard.press("Control+A")
                    await page.keyboard.type(time_str)
                    logger.info(f"✅ Hora digitada: {time_str}")
                    
                    # Sai do campo
                    await page.locator("body").click()
                    
                except Exception as e:
                    logger.error(f"❌ Erro na digitação via teclado: {e}")

                target_button_text = "Agendar"

            # --- COLAR ISSO ANTES DO CLIQUE FINAL EM "AGENDAR" ---
            logger.info("⏳ Aguardando verificação de direitos autorais do TikTok...")

            try:
                # 1. Espera a verificação começar (as vezes demora uns segundos pra aparecer)
                await page.wait_for_timeout(3000) 
                
                # 2. Tenta esperar pelo texto de sucesso. 
                # O timeout é alto (60s) porque as vezes o TikTok demora.
                # Ajuste o texto abaixo conforme o que aparece na sua tela (no vídeo é "Nenhum problema encontrado")
                await page.get_by_text("Nenhum problema encontrado").wait_for(timeout=60000)
                
                logger.info("✅ Verificação concluída! O caminho está livre.")

            except Exception as e:
                logger.warning(f"⚠️ Alerta: A verificação demorou demais ou não apareceu. Tentando agendar mesmo assim... Erro: {e}")

            # --- AÇÃO FINAL ---
            logger.info(f"🚀 Confirmando ação: {target_button_text}...")
            await asyncio.sleep(2) # Espera UI atualizar texto do botão

            # Tenta clicar no botão final
            clicked = False
            buttons = [target_button_text, "Programar", "Agendar", "Publicar", "Post", "Schedule"]
            
            for btn_txt in buttons:
                try:
                    btn = page.locator(f"button:has-text('{btn_txt}')").first
                    if await btn.is_visible():
                        await btn.click()
                        clicked = True
                        break
                except: continue
            
            if not clicked:
                # Tenta botão vermelho genérico via CSS
                await page.locator("button[class*='Button__root--type-primary']").last.click()

            # --- CONFIRMAÇÃO DE MODAL ---
            logger.info("👀 Verificando modais extras...")
            await asyncio.sleep(2)
            try:
                modal_btn = page.locator('div[role="dialog"] button:has-text("Agendar"), div[role="dialog"] button:has-text("Publicar")').first
                if await modal_btn.is_visible():
                    logger.info("🛑 Modal detectado! Clicando novamente...")
                    await modal_btn.click()
            except: pass

            logger.info("⏳ Aguardando processamento final...")
            await asyncio.sleep(5)
            
            return {
                "success": True, 
                "message": f"Upload finalizado ({target_button_text})"
            }

        except Exception as e:
            error_msg = f"Erro no Upload: {str(e)}"
            logger.error(f"❌ {error_msg}")
            await page.screenshot(path="backend/static/error_screenshot.png")
            return {"success": False, "message": error_msg}
            
        finally:
            await browser.close()
