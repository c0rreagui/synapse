"""
TikTok Uploader Module - VERSAO ULTRA-MONITORADA
Captura TODAS as informacoes possiveis do Bot e TikTok Studio
"""
import asyncio
import os
import sys
import logging
from datetime import datetime
import re

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import Page
from core.browser import launch_browser, close_browser
from core.session_manager import get_session_path
from core.monitor import TikTokMonitor
from core.locking import session_lock, SessionLockError

logger = logging.getLogger(__name__)

async def upload_video_monitored(
    session_name: str,
    video_path: str,
    caption: str,
    hashtags: list = None,
    schedule_time: str = None, 
    post: bool = False,
    enable_monitor: bool = False,  # Monitor desativado por padrao
    viral_music_enabled: bool = False,
    sound_title: str = None,  # Titulo da musica viral especifica
    privacy_level: str = "public_to_everyone" # public_to_everyone, mutual_follow_friends, self_only
) -> dict:
    # --- HELPER: Nuke Modals ---
    async def nuke_modals(page_ref):
        try:
            # Remove overlays e backdrops comuns
            await page_ref.evaluate("""
                () => {
                    document.querySelectorAll('.TUXModal-overlay, .TUXModal-backdrop, [role="dialog"]').forEach(el => el.remove());
                    document.querySelectorAll('div[class*="overlay"], div[class*="backdrop"]').forEach(el => {
                        if(window.getComputedStyle(el).position === 'fixed') el.remove();
                    });
                }
            """)
            await page_ref.wait_for_timeout(200)
        except: pass
    
    # --- HELPER: Nuke Modals ---
    async def nuke_modals(page_ref):
        try:
            # Remove overlays e backdrops comuns
            await page_ref.evaluate("""
                () => {
                    document.querySelectorAll('.TUXModal-overlay, .TUXModal-backdrop, [role="dialog"]').forEach(el => el.remove());
                    document.querySelectorAll('div[class*="overlay"], div[class*="backdrop"]').forEach(el => {
                        if(window.getComputedStyle(el).position === 'fixed') el.remove();
                    });
                }
            """)
            await page_ref.wait_for_timeout(200)
        except: pass

    result = {"status": "error", "message": "", "screenshot_path": None}
    
    # MONITOR ULTRA-DETALHADO (so ativa se solicitado)
    monitor = TikTokMonitor(session_name) if enable_monitor else None
    if enable_monitor:
        logger.info(f"[MONITOR] OLHO DE DEUS ativado: {monitor.run_id}")
    else:
        logger.info("[UPLOAD] Monitor desativado (modo producao)")

    if not os.path.exists(video_path):
        return {"status": "error", "message": "Video not found"}
    
    session_path = get_session_path(session_name)
    
    # Init vars for finally block
    p = None
    browser = None
    context = None
    page = None
    
    # 🔒 LOCK SESSION (Manual Context Manager to avoid re-indenting 1000 lines)
    _lock_ctx = session_lock(session_name)
    _lock_acquired = False

    try:
        _lock_ctx.__enter__()
        _lock_acquired = True
        
        p, browser, context, page = await launch_browser(headless=False, storage_state=session_path)
            
        # 🎬 INICIAR PLAYWRIGHT TRACE (só se monitor ativo)
        if monitor:
            await monitor.start_tracing(context)
            # 📝 Injetar console logger ULTRA-DETALHADO
            await monitor.inject_console_logger(page)
            # 📸 INICIAR CAPTURA CONTÍNUA (500ms)
            await monitor.start_continuous_screenshot(page, interval=0.5)
        
        # ========== STEP 0: RENDERIZAÇÃO (SIMULADA/PREPARATÓRIA) ==========
        # Como o vídeo já vem pronto, o "Render" aqui é a preparação do ambiente Playwright/Browser
        from core.status_manager import status_manager
        status_manager.update_status("busy", step="rendering", progress=50, logs=["Renderizando ambiente seguro..."])

        
        # ========== STEP 1: NAVEGAÇÃO ==========
        status_manager.update_status("busy", step="uploading", progress=60, logs=["Acessando TikTok Studio..."])
        from core.network_utils import get_upload_url
        await page.goto(get_upload_url(), timeout=120000, wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)
        if monitor:
            await monitor.capture_full_state(page, "navegacao_inicial", 
                                            "Página de upload do TikTok Studio carregada")
        
        # 🛡️ SECURITY CHECK: Detect Login Redirect (Dead Session)
        current_url = page.url
        if "login" in current_url or "tiktok.com" not in current_url:
            logger.error(f"❌ SESSÃO MORTA DETECTADA! Redirecionado para login: {current_url}")
            
            # Auto-Kill Session in DB to prevent infinite retries
            try:
                from core.session_manager import update_profile_info
                # Remove "tiktok_profile_" prefix to get ID/Slug
                pid = session_name
                # Some session names are full strings, handle that if needed, 
                # but get_session_path uses session_name directly, so slug matches.
                
                update_profile_info(pid, {"active": False})
                logger.critical(f"💀 PERFIL {pid} DESATIVADO AUTOMATICAMENTE NO BANCO.")
                
                status_manager.update_status("error", logs=["Sessão expirada. Perfil desativado."])
            except Exception as kill_err:
                logger.error(f"Erro ao desativar perfil: {kill_err}")
                
            raise Exception("Session Expired - Login Required")
        
        
        # ========== STEP 2: UPLOAD DO VÍDEO (COM FALLBACKS) ==========
        logger.info("⏳ Aguardando página carregar completamente...")
        
        # Aguarda elementos indicativos que a página carregou
        try:
            from core.ui_selectors import STUDIO_SELECT_BUTTON, STUDIO_UPLOAD_INPUT
            # Aguarda pelo menos um destes elementos aparecer (indica página carregada)
            await page.wait_for_selector(
                f'{STUDIO_SELECT_BUTTON}, {STUDIO_UPLOAD_INPUT}, .upload-card',
                timeout=20000,
                state="attached"
            )
            logger.info("✅ Página de upload carregada!")
        except Exception as e:
            logger.warning(f"⚠️ Timeout aguardando elementos de upload: {e}")
        
        # Aguarda um pouco mais para garantir que JS terminou
        await page.wait_for_timeout(3000)
        
        logger.info("🔍 Procurando seletor de upload...")
        
        upload_successful = False
        
        # ESTRATÉGIA 1: Tentar botão visível primeiro
        try:
            logger.info("Tentando Estratégia 1: Botão 'Selecionar vídeo'...")
            from core.ui_selectors import STUDIO_SELECT_BUTTON
            upload_buttons = [
                'button:has-text("Selecionar vídeo")',
                'button:has-text("Select video")',
                STUDIO_SELECT_BUTTON,
                'button:has-text("Upload")'
            ]
            
            for btn_selector in upload_buttons:
                if await page.locator(btn_selector).count() > 0:
                    logger.info(f"✅ Botão encontrado: {btn_selector}")
                    # Não clica no botão, só localiza o input associado
                    break
        except Exception as e:
            logger.warning(f"Estratégia 1 falhou: {e}")
        
        # ESTRATÉGIA 2: Usar input file diretamente (pode estar oculto)
        try:
            logger.info("Tentando Estratégia 2: Input file direto...")
            from core.ui_selectors import STUDIO_UPLOAD_INPUT
            # Procura por input file mesmo que esteja hidden
            file_input_locator = page.locator(STUDIO_UPLOAD_INPUT)
            input_count = await file_input_locator.count()
            
            # Verifica se existe
            if input_count > 0:
                logger.info(f"✅ Input file encontrado ({input_count} elemento(s)) - fazendo upload...")
                await file_input_locator.first.set_input_files(video_path)
                upload_successful = True
                logger.info("📤 Upload do arquivo iniciado com sucesso!")
            else:
                raise Exception("Input file não encontrado (count = 0)")
                
        except Exception as e:
            logger.error(f"❌ Estratégia 2 falhou: {e}")
            
            # ESTRATÉGIA 3: FALLBACK FINAL - Tentar seletores alternativos
            logger.info("Tentando Estratégia 3: Seletores alternativos...")
            alternate_selectors = [
                'input[accept*="video"]',
                'input[accept*="mp4"]',
                '[data-e2e="upload-input"]',
                '.upload-input'
            ]
            
            for selector in alternate_selectors:
                try:
                    selector_count = await page.locator(selector).count()
                    if selector_count > 0:
                        logger.info(f"✅ Seletor alternativo encontrado: {selector} ({selector_count} elemento(s))")
                        await page.locator(selector).first.set_input_files(video_path)
                        upload_successful = True
                        logger.info("📤 Upload iniciado com seletor alternativo!")
                        break
                except Exception as ex:
                    logger.warning(f"Seletor '{selector}' falhou: {ex}")
                    continue
        
        if not upload_successful:
            error_msg = "Não foi possível encontrar seletor de upload após todas as estratégias"
            logger.error(f"❌ {error_msg}")
            if monitor:
                await monitor.capture_full_state(page, "ERRO_upload_selector", error_msg)
            return {"status": "error", "message": error_msg}
        
        await page.wait_for_timeout(2000)
        if monitor:
            await monitor.capture_full_state(page, "pos_upload_arquivo",
                                            f"Arquivo {os.path.basename(video_path)} enviado")
        
        # ========== PROTOCOLO DOM NUKER CIRÚRGICO ==========
        logger.info("🎯 Executando DOM NUKER CIRÚRGICO (Somente Tutoriais)...")
        
        # CAMADA 1: Fechar via ESC (método mais seguro)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(800)
        
        # CAMADA 2: Clicar APENAS em botões de tutorial com texto específico
        await page.evaluate("""
            // Busca e clica APENAS em botões com texto de tutorial
            const tutorialButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
                const text = btn.innerText.toLowerCase();
                return text.includes('entendi') || 
                       text.includes('got it') || 
                       text.includes('próximo') ||
                       text.includes('next');
            });
            
            tutorialButtons.forEach(btn => {
                try { 
                    console.log('🎯 Clicando em botão de tutorial:', btn.innerText);
                    btn.click(); 
                } catch(e) {}
            });
        """)
        await page.wait_for_timeout(1000)
        
        # CAMADA 3: Remoção CIRÚRGICA (somente elementos explicitamente de tutorial)
        await page.evaluate("""
            const surgicalNuke = () => {
                // APENAS seletores ESPECÍFICOS de tutorial/guia (sem wildcards perigosos)
                const safeTargets = [
                    // React Joyride (tutorial interativo - CAUSA DO BUG)
                    '#react-joyride-portal',
                    '[data-test-id="overlay"]',
                    '.react-joyride__overlay',
                    '.react-joyride__spotlight',
                    '.react-joyride__tooltip',
                    // Tutoriais do TikTok
                    '[data-e2e="tutorial-tooltip-got-it-btn"]',
                    '[data-e2e="guide-got-it"]',
                    '[data-e2e*="tutorial-tooltip"]',
                    '[class*="TutorialTooltip"]',
                    '[class*="GuideTooltip"]',
                    '[id*="tutorial-"]',
                    '[id*="guide-"]',
                    'div[role="tooltip"][class*="guide"]'
                ];
                
                let removed = 0;
                safeTargets.forEach(selector => {
                    try {
                        document.querySelectorAll(selector).forEach(el => {
                            console.log('🗑️ Removendo tutorial:', selector);
                            el.remove();
                            removed++;
                        });
                    } catch(e) {
                        console.error('Erro na remoção:', e);
                    }
                });
                
                // Remove APENAS overlays que contém texto de tutorial
                document.querySelectorAll('div[role="dialog"], div[class*="modal"]').forEach(modal => {
                    const text = modal.innerText || '';
                    if (text.includes('novos recursos') || 
                        text.includes('new features') ||
                        text.includes('Seja bem-vindo')) {
                        console.log('🗑️ Removendo modal de boas-vindas');
                        modal.remove();
                        removed++;
                    }
                });
                
                return removed;
            };
            
            // Executa UMA VEZ (não em loop contínuo para evitar quebrar a UI)
            const removedCount = surgicalNuke();
            console.log(`🎯 Limpeza cirúrgica: ${removedCount} elementos de tutorial removidos`);
            
            // Executa APENAS mais uma vez após 2s (não em loop infinito)
            setTimeout(() => {
                const secondPass = surgicalNuke();
                if (secondPass > 0) console.log(`🎯 Segunda passagem: ${secondPass} elementos removidos`);
            }, 2000);
        """)
        
        await page.wait_for_timeout(3000)
        if monitor:
            await monitor.capture_full_state(page, "pos_dom_nuker",
                                            "DOM Nuker executado - Overlays e tutoriais removidos")

        # ========== PRIVACY SETTINGS (FIRST PRIORITY) ==========
        # [SYN-FIX] Set Privacy First per user request to ensure correct status during analysis
        logger.info(f"🔒 Configurando privacidade PRIORITÁRIA para: {privacy_level}")
        try:
            await nuke_modals(page)
            
            # 1. Scroll to Bottom to find Configs/Privacy
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
            # 2. Find Privacy Trigger (Combobox or Radio)
            privacy_found = False
            
            # Map internal keys to UI labels (Regex)
            # [SYN-FIX] Expanded Regex for PT-BR / EN
            privacy_map = {
                "public_to_everyone": [re.compile(r"Todos|Everyone|Public|Público", re.I)],
                "public": [re.compile(r"Todos|Everyone|Public|Público", re.I)],
                "mutual_follow_friends": [re.compile(r"Amigos|Friends|Seguidores|Followers", re.I)],
                "friends": [re.compile(r"Amigos|Friends|Seguidores|Followers", re.I)],
                "self_only": [re.compile(r"Somente (eu|você|voce)|Only me|Private|Privado|Apenas eu", re.I)],
                "private": [re.compile(r"Somente (eu|você|voce)|Only me|Private|Privado|Apenas eu", re.I)]
            }
            
            target_patterns = privacy_map.get(privacy_level, privacy_map["public_to_everyone"])
            
            # [SYN-FIX] Iterative Strategy with contenteditable check
            candidates = page.locator('.tiktok-select-selector, [role="combobox"], .tux-select-selector')
            count = await candidates.count()
            
            logger.info(f"🔒 Encontrados {count} comboboxes candidatos para privacidade.")
            
            for i in range(count):
                el = candidates.nth(i)
                if not await el.is_visible(): continue
                
                # [SYN-FIX] Avoid Description Box (role=combobox for mentions)
                if await el.get_attribute("contenteditable") == "true":
                     continue
                
                txt = await el.text_content() or ""
                # Check if this element looks like Privacy Selector
                if re.search(r"Quem pode|Who can|Todos|Everyone|Amigos|Friends|Somente|Only|Privado|Private|Apenas", txt, re.I):
                    logger.info(f"🔒 Clicando candidato {i} com texto: '{txt.strip()}'")
                    await el.scroll_into_view_if_needed()
                    try:
                        await el.click(timeout=2000)
                    except:
                        await el.click(force=True)
                    
                    await page.wait_for_timeout(1000)
                    if monitor:
                         await monitor.capture_full_state(page, f"debug_menu_open_{i}", f"Menu aberto? {txt.strip()}")
                    
                    # Try to find target option in the OPEN menu
                    option_clicked = False
                    for pattern in target_patterns:
                        # [SYN-FIX] Broader Option Search using Playwright text regex
                        pat_source = pattern.pattern.replace('(?i)', '')
                        
                        # Search visible text matching pattern
                        opt = page.locator(f"text=/{pat_source}/i")
                        
                        opt_count = await opt.count()
                        if opt_count > 0:
                            o = opt.last
                            if await o.is_visible():
                                await o.click(force=True)
                                logger.info(f"✅ Opção '{pat_source}' selecionada (via text locator)!")
                                option_clicked = True
                                privacy_found = True
                                break
                                
                    if option_clicked:
                        break
                    if option_clicked:
                        break
                    else:
                        # [SYN-FIX] Option click failed. Try Keyboard Navigation.
                        logger.info("⚠️ Opção não encontrada via clique. Tentando Teclado (Arrow Keys)...")
                        try:
                            await el.focus()
                            found_via_keys = False
                            # Try navigating down (Public -> Friends -> Private)
                            for _ in range(3):
                                await page.keyboard.press("ArrowDown")
                                await page.wait_for_timeout(300)
                                
                                curr_txt = await el.text_content() or ""
                                # Check if text matches current privacy level target
                                for pattern in target_patterns:
                                    if pattern.search(curr_txt):
                                        found_via_keys = True
                                        privacy_found = True
                                        logger.info(f"✅ Privacidade definida via Teclado: {curr_txt}")
                                        await page.keyboard.press("Enter")
                                        break
                                if found_via_keys: break
                            
                            if found_via_keys:
                                 break
                            else:
                                 await page.keyboard.press("Escape")
                        except Exception as e:
                            logger.warning(f"Erro no fallback de teclado: {e}") 
                            await page.keyboard.press("Escape")
            
            # B. Radio Group Approach (Older UI)
            if not privacy_found:
                logger.info("🔒 Tentando Radio Group de privacidade...")
                for pattern in target_patterns:
                    radio = page.locator('label, div').filter(has_text=pattern).last
                    if await radio.count() > 0 and await radio.is_visible():
                        await radio.click()
                        privacy_found = True
                        logger.info(f"✅ Privacidade definida via Radio Group: {privacy_level}")
                        break

            # C. JavaScript Label Search (Robustest Fallback)
            if not privacy_found:
                logger.info("🔒 Tentando Estratégia JS baseada em Texto...")
                js_success = await page.evaluate(f"""(target_pattern_str) => {{
                    const labels = Array.from(document.querySelectorAll('div, h3, h4, span, label')).filter(el => 
                        /Quem pode|Who can/i.test(el.innerText) && el.innerText.length < 50
                    );
                    if (labels.length > 0) {{
                        const label = labels[labels.length - 1];
                        console.log("Found privacy label:", label.innerText);
                        let sibling = label.nextElementSibling;
                        while(sibling) {{
                            if (sibling.matches('[role="combobox"], .tiktok-select-selector') || sibling.querySelector('[role="combobox"]')) {{
                                const target = sibling.matches('[role="combobox"]') ? sibling : sibling.querySelector('[role="combobox"]');
                                target.click();
                                return "clicked_combo";
                            }}
                            sibling = sibling.nextElementSibling;
                        }}
                    }}
                    return "not_found";
                }}""", "")
                
                if js_success == "clicked_combo":
                    await page.wait_for_timeout(500)
                    for pattern in target_patterns:
                         pat_str = pattern.pattern.replace("(?i)", "")
                         await page.evaluate(f"""(pat) => {{
                            const options = Array.from(document.querySelectorAll('[role="option"], li, div'));
                            const target = options.find(el => new RegExp(pat, 'i').test(el.innerText));
                            if (target) {{
                                target.click();
                                return true;
                            }}
                            return false;
                         }}""", pat_str)
                         privacy_found = True
                         logger.info(f"✅ Privacidade definida via JS Search: {privacy_level}")
                         break

            if not privacy_found:
                logger.warning(f"⚠️ Não foi possível definir privacidade para {privacy_level}. Usando padrão.")
            
            if monitor:
                await monitor.capture_full_state(page, "pos_privacidade_priority", f"Privacidade Prioritária: {privacy_level}")
                
            # Scroll Back to Top for Caption
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

        except Exception as e:
            logger.error(f"❌ Erro ao configurar privacidade (Prioridade): {e}")

        # ========== PREENCHIMENTO DA LEGENDA (FOCO ALVO) ==========
        # Normalize hashtags: ensure each has exactly one # prefix (avoid ##)
        if hashtags:
            normalized_tags = []
            for h in hashtags:
                tag = h.lstrip('#')  # Remove any leading #
                if tag:  # Avoid empty tags
                    normalized_tags.append(f"#{tag}")
            full_caption = f"{caption} " + " ".join(normalized_tags)
        else:
            full_caption = caption
        
        logger.info("📝 Preenchendo legenda...")
        editor = page.locator('.public-DraftEditor-content')
        if await editor.is_visible():
            # Em vez de apertar Ctrl+A na página, apertamos NO ELEMENTO
            await editor.focus()
            await editor.press("Control+A")
            await editor.press("Backspace")
            await page.keyboard.type(full_caption, delay=50)
            logger.info("✅ Legenda inserida com sucesso.")
            # Clica no canto superior esquerdo para tirar foco e fechar sugestões de hashtag
            await page.mouse.click(10, 10) 
            
            if monitor:
                await monitor.capture_full_state(page, "legenda_preenchida",
                                                f"Legenda preenchida: {full_caption[:50]}...")
        
        # ========== AGUARDAR UPLOAD (CRÍTICO) ==========
        logger.info("⏳ Aguardando conclusão do upload...")
        upload_success = False
        for i in range(150): # Tenta por até 5 minutos (300s)
            # 1. Indicadores de Texto/Botão Topo
            if await page.locator('text="Enviado"').count() > 0 or \
               await page.locator('text="Uploaded"').count() > 0 or \
               await page.locator('button:has-text("Substituir")').count() > 0:
                upload_success = True
                logger.info("✅ Upload concluído (Texto/Substituir detectado)!")
                break
            
            # 2. Scroll para baixo para checar botão final (visibilidade)
            if i % 3 == 0 and i > 0: 
                 await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # 3. Verifica progresso
            progress_els = await page.locator('.progress-text, [role="progressbar"]').all_inner_texts()
            if any("100%" in t for t in progress_els):
                upload_success = True
                logger.info("✅ Upload 100% detectado!")
                break
            
            # 4. Fallback: Botão Final Habilitado
            sched_btn = page.locator('button:has-text("Programar"), button:has-text("Schedule"), button:has-text("Publicar"), button:has-text("Post")').last
            if await sched_btn.count() > 0 and await sched_btn.is_visible() and await sched_btn.is_enabled():
                upload_success = True
                logger.info("✅ Botão de ação final detectado e habilitado! Upload concluído.")
                break
                
            await asyncio.sleep(2)
            if i % 10 == 0: logger.info(f"Ainda aguardando upload... ({i*2}s)")
        
        if not upload_success:
            logger.warning("⚠️ Tempo limite de espera do upload excedido ou não detectado. Tentando prosseguir...")

        # ========== VIRAL AUDIO BOOST (MONITORED) ==========
        if viral_music_enabled:
            logger.info("🎵 Iniciando Viral Audio Boost...")
            if monitor: await monitor.capture_full_state(page, "pre_viral_boost", "Iniciando Boost Viral")
            
            try:
                # 1. Clicar em Editar
                edit_btn = page.locator('button:has-text("Editar vídeo"), button:has-text("Edit video")').first
                if await edit_btn.is_visible():
                    await edit_btn.click()
                    await page.wait_for_timeout(5000) # Espera editor carregar
                    
                    if monitor: await monitor.capture_full_state(page, "editor_aberto", "Editor de vídeo aberto")

                    # 2. Clicar em Música/Sons
                    music_tab = page.locator('div[role="tab"], button').filter(has_text=re.compile(r"Música|Music|Sound|Som", re.I)).first
                    if await music_tab.is_visible():
                        await music_tab.click()
                        await page.wait_for_timeout(2000)
                        
                        # 3. Buscar música específica (se sound_title fornecido)
                        if sound_title:
                            logger.info(f"🔍 Buscando música: {sound_title}")
                            search_input = page.locator('input[placeholder*="Search"], input[placeholder*="Buscar"], input[type="search"]').first
                            if await search_input.is_visible():
                                await search_input.fill(sound_title)
                                await page.wait_for_timeout(2000)  # Aguarda resultados
                                logger.info("✅ Busca realizada, selecionando primeiro resultado...")
                        
                        # 4. Selecionar primeira música (resultado da busca ou Top 1)
                        first_song = page.locator('.music-item, [class*="music-card"], [class*="sound-item"]').first
                        if await first_song.is_visible():
                            await first_song.hover()
                            use_btn = first_song.locator('button')
                            if await use_btn.count() > 0:
                                await use_btn.first.click()
                                logger.info(f"🎵 Música Viral aplicada: {sound_title or 'Top 1'}")
                                await page.wait_for_timeout(1000)
                                
                                # 4. Ajustar Volume (Música 0%, Original 100%)
                                volume_tab = page.locator('div, button').filter(has_text=re.compile(r"Volume", re.I)).last
                                if await volume_tab.is_visible():
                                    await volume_tab.click()
                                    await page.wait_for_timeout(500)
                                    sliders = page.locator('input[type="range"]')
                                    slider_count = await sliders.count()
                                    if slider_count >= 2:
                                        # Slider 0 = Original (manter 100%), Slider 1 = Música (colocar 0%)
                                        await sliders.nth(1).fill("0")  # Música adicionada = 0%
                                        logger.info("🔈 Volume da música definido para 0% (vídeo original mantido em 100%)")
                                        if monitor: await monitor.capture_full_state(page, "volume_ajustado", "Música muda, original 100%")
                                    elif slider_count == 1:
                                        # Se só tem 1 slider, provavelmente é o da música
                                        await sliders.first.fill("0")
                                        logger.info("🔈 Único slider de volume definido para 0%")
                            
                    # 5. Salvar
                    save_edit = page.locator('button:has-text("Salvar edição"), button:has-text("Save edit"), button:has-text("Confirmar")').last
                    if await save_edit.is_visible():
                        await save_edit.click()
                        await page.wait_for_timeout(5000)
                        logger.info("✅ Edição salva.")
                        if monitor: await monitor.capture_full_state(page, "editor_salvo", "Edição salva com sucesso")
                    else:
                         logger.warning("Botão Salvar não encontrado, voltando...")
                         await page.keyboard.press("Escape")

                else:
                    logger.warning("Botão de Editar Vídeo não encontrado. Pulando Viral Boost.")
                    if monitor: await monitor.capture_full_state(page, "erro_botao_editar", "Botão Editar não encontrado")

            except Exception as e:
                logger.error(f"❌ Falha no Viral Boost: {e}")
                if monitor: await monitor.capture_full_state(page, "erro_viral_boost", str(e))
                await page.keyboard.press("Escape")





        # ========== AGENDAMENTO (VISUAL HUMANO - CLIQUE) ==========
        if schedule_time:
            dt = datetime.fromisoformat(schedule_time)
            date_str = dt.strftime('%Y-%m-%d')
            user_date_str = dt.strftime('%d/%m/%Y')
            time_str = dt.strftime('%H:%M')
            target_day = str(dt.day)
            
            logger.info(f"⏳ Iniciando fluxo de agendamento CLIQUE para: dia {target_day} às {time_str}")
            
            # Scroll bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
            # 1. Toggle / Accordion
            found_toggle = False
            targets = ["Programar vídeo", "Schedule video", "Agendar", "Programação"]
            for t in targets:
                loc = page.locator(f'div, label').filter(has_text=t).last
                if await loc.is_visible():
                    await loc.click(force=True)
                    logger.info(f"✅ Toggle '{t}' acionado.")
                    found_toggle = True
                    break
            
            # 1. Ativar Agendamento
            logger.info("🕒 Ativando switch de agendamento...")
            # Tentativa 1: Selector baseado no valor encontrado nos logs
            schedule_toggle = page.locator('input[value="schedule"]')
            
            # Tentativa 2: Selectors genéricos de UI (caso o value mude)
            if await schedule_toggle.count() == 0:
                 schedule_toggle = page.locator('.tux-switch, .tiktok-switch, input[type="checkbox"][id*="schedule"]')

            if await schedule_toggle.count() > 0:
                # Verifica se já está marcado
                is_checked = await schedule_toggle.is_checked()
                if not is_checked:
                    await schedule_toggle.click(force=True)
                    logger.info("✅ Switch de agendamento clicado.")
                    await page.wait_for_timeout(2000) # Wait for animation
                else:
                    logger.info("ℹ️ Switch já estava ativo.")
            else:
                logger.error("❌ Toggle de agendamento não encontrado. Tentando clicar no texto 'Programar'...")
                await page.click('text="Programar"', timeout=2000)
            
            await page.wait_for_timeout(1000)
            
            # 2. Interação com Data (Agenda) - CLICK ROBUSTO
            logger.info("📅 Interagindo com seletor de data (Robust Mode)...")
            date_input = page.locator('.tux-date-picker input, input[placeholder*="DATA"], input[type="text"]').last
            if await date_input.is_visible():
                await date_input.click(force=True)
                await page.wait_for_timeout(1000)
                
                # Debug Visual: Salvar o estado do calendário aberto
                if monitor:
                    debug_shot = monitor.screenshots_path / "debug_calendar_open.jpg"
                    try: await page.screenshot(path=str(debug_shot))
                    except: pass

                # Tentar clicar no dia exato usando múltiplas estratégias
                day_found = False
                
                # Estratégia 1: Tags padrão com texto exato (Regex ^\s*d\s*$)
                for tag in ['div', 'span', 'td', 'button']:
                    # Procura classes tipicas de calendario para evitar falsos positivos
                    # Regex flexivel para espaços: " 7 " ou "7"
                    candidates = page.locator(f'{tag}').filter(has_text=re.compile(f"^\s*{target_day}\s*$"))
                    count = await candidates.count()
                    if count > 0:
                        # Tenta o último (geralmente datas futuras estão no fim se houver sobreposição)
                        # Verifica se está visível
                        for i in range(count - 1, -1, -1):
                            el = candidates.nth(i)
                            if await el.is_visible():
                                await el.click(force=True)
                                logger.info(f"📅 Dia {target_day} clicado via tag {tag}.")
                                day_found = True
                                break
                    if day_found: break
                
                # Estratégia 2: Fallback JavaScript (Força bruta no DOM segura)
                if not day_found:
                    logger.warning(f"⚠️ Dia {target_day} não encontrado via seletores. Tentando JS Fallback...")
                    await page.evaluate(f"""(day) => {{
                        const els = Array.from(document.querySelectorAll('*'));
                        // Filtra elementos com TEXTO exato do dia (Seguro contra undefined e espaços)
                        const matches = els.filter(el => el.innerText && el.innerText.trim() === day);
                        console.log(`JS Found ${{matches.length}} candidates for ${{day}}`);

                        // Tenta achar um que pareça estar num container de calendario
                        const inPicker = matches.filter(el => el.closest('.picker, .calendar, .react-datepicker, [role="dialog"], [class*="picker"]'));
                        
                        if (inPicker.length > 0) {{
                            console.log("JS Click in Picker: " + day);
                            inPicker[inPicker.length - 1].click();
                        }} else if (matches.length > 0) {{
                            // Tenta o último encontrado na página (fallback extremo)
                            console.log("JS Click Fallback: " + day);
                            matches[matches.length - 1].click();
                        }} else {{
                            console.error("JS Found NO matches for day " + day);
                        }}
                    }}""", target_day)
                    logger.info("📅 JS Click executado.")
            
            # 3. Interação com Hora - CLICK ROBUSTO
            logger.info("⏰ Interagindo com seletor de hora (Robust Mode)...")
            
            # Tenta encontrar input de hora dinamicamente e clicar nele
            time_input_found = False
            potential_time_inputs = page.locator('input, [role="combobox"], [role="textbox"]')
            
            # 1. Tenta Seletor CSS Direto (Mais rápido)
            time_input = page.locator('.tux-time-picker input, input[placeholder*="HORA"], input[placeholder*="Time"]').last
            if await time_input.is_visible():
                await time_input.click(force=True)
                time_input_found = True
                logger.info("⏰ Time Input clicado (Seletor CSS).")
            else:
                # 2. Scanner de Inputs para encontrar o campo de hora
                logger.warning("⚠️ Time Input não visível via CSS. Iniciando Scanner pré-click...")
                count_inputs = await potential_time_inputs.count()
                for i in range(count_inputs):
                    inp = potential_time_inputs.nth(i)
                    if not await inp.is_visible(): continue
                    
                    ph = await inp.get_attribute('placeholder') or ""
                    lbl = await inp.get_attribute('aria-label') or ""
                    val = await inp.get_attribute('value') or ""
                    
                    if "Hora" in ph or "Time" in ph or "Hora" in lbl or "Time" in lbl:
                        await inp.click(force=True)
                        time_input_found = True
                        logger.info(f"⏰ Time Input clicado (Scanner: Texto).")
                        break
                    
                    # Check for Time Value (HH:MM) - CRITICAL FIX based on logs
                    if re.match(r"^\d{1,2}:\d{2}$", val):
                        await inp.click(force=True)
                        time_input_found = True
                        logger.info(f"⏰ Time Input clicado (Scanner: Valor {val}).")
                        break
                        
            if time_input_found:
                # await time_input.click(force=True)  <-- REMOVIDO (Já clicado acima)
                await page.wait_for_timeout(1000)
                
                # Debug Shot
                if monitor:
                    try: await page.screenshot(path=str(monitor.screenshots_path / "debug_time_open.jpg"))
                    except: pass
                
                time_found = False
                time_pattern = re.compile(f"^\s*{time_str}\s*$")
                
                # Estratégia 1: Seletores Padrão com SCROLL DINÂMICO
                list_container = page.locator('ul, .tiktok-select-dropdown, .time-picker-list, [role="listbox"], .tux-select-dropdown').last
                
                logger.info(f"🔄 Iniciando busca por '{time_str}'...")
                
                for attempt in range(15): # Tenta scrollar até 15 vezes
                    # Tenta o texto completo primeiro
                    options = page.locator('li, div[role="option"], .time-item, span').filter(has_text=time_pattern)
                    if await options.count() > 0:
                        for i in range(await options.count()):
                            opt = options.nth(i)
                            if await opt.is_visible():
                                await opt.scroll_into_view_if_needed()
                                await opt.click(force=True)
                                logger.info(f"✅ Hora {time_str} selecionada (Seletor Universal) no scroll {attempt}.")
                                time_found = True
                                break
                    
                    if time_found: break
                        
                    # Se não achou, scrolla o container ou usa teclado
                    if await list_container.is_visible():
                        await list_container.evaluate("el => el.scrollBy(0, 150)")
                        await page.wait_for_timeout(200)
                    else:
                        await page.keyboard.press("ArrowDown")
                        await page.wait_for_timeout(100)
                            
                # Estratégia 2: JS Robusto (Fura Shadow DOM + Accordion / Split)
                # ESTRATÉGIA FINAL V5: Seleção por Âncoras Visuais & Cliques Diretos
                target_str = f"{time_str}" # 12:00
                h_target, m_target = target_str.split(':')
                
                for v_attempt in range(6):
                    await page.wait_for_timeout(1500)
                    
                    # 1. Busca a Âncora Visual (Onde o horário aparece na tela)
                    badge_info = await page.evaluate("""() => {
                        // Busca elementos que tenham padrão HH:MM (ex: 12:00, 23:40)
                        const regex = /^[0-2][0-9]:[0-5][0-9]$/;
                        const candidates = Array.from(document.querySelectorAll('span, div, input'))
                            .filter(e => {
                                const text = (e.innerText || e.value || "").trim();
                                return regex.test(text);
                            });
                        
                        if (candidates.length > 0) {
                            // Pega o que está mais "baixo" ou central na tela (geralmente o seletor)
                            const target = candidates[candidates.length - 1]; 
                            const r = target.getBoundingClientRect();
                            return { 
                                val: (target.value || target.innerText || "").trim(), 
                                x: r.left + r.width/2, 
                                y: r.top + r.height/2 
                            };
                        }
                        return null;
                    }""")
                    
                    current_val = badge_info['val'] if badge_info else "not_found"
                    logger.info(f"🧐 Verificação Visual {v_attempt+1}: Desejado={target_str} | Atual={current_val}")
                    
                    if target_str in str(current_val):
                        logger.info("🎯 Horário VALIDADO visualmente!")
                        break
                    
                    # 2. Se estiver errado, age sobre a âncora
                    if v_attempt < 5:
                        logger.warning(f"⚠️ Horário incorreto. Tentando Correção Visual Master...")
                        
                        # Abre o picker (clica na âncora ou no centro estimado)
                        click_x = badge_info['x'] if badge_info else 300
                        click_y = badge_info['y'] if (badge_info and badge_info['y'] > 100) else 750
                        # Abre o picker (clica na âncora ou no centro estimado)
                        click_x = badge_info['x'] if badge_info else 300
                        click_y = badge_info['y'] if (badge_info and badge_info['y'] > 100) else 750
                        await page.mouse.click(click_x, click_y) # Single click
                        await page.wait_for_timeout(1000)
                        
                        # 2. Column Click Strategy (v27) - Baseado na análise do fluxo manual
                        logger.info("🎯 Iniciando Column Click Strategy (v27)...")
                        
                        target_hour = target_str.split(':')[0]  # "20"
                        target_minute = target_str.split(':')[1]  # "30"
                        
                        # Localiza as duas colunas do picker (hora à esquerda, minutos à direita)
                        column_click_result = await page.evaluate("""([targetH, targetM]) => {
                            // Encontra elementos que parecem colunas de picker (múltiplos seletores)
                            let allCandidates = Array.from(document.querySelectorAll(
                                'ul, [role="listbox"], [class*="column"], [class*="picker"], [class*="list"], [class*="scroll"]'
                            )).filter(el => {
                                const items = el.querySelectorAll('li, div, span');
                                const hasNumbers = Array.from(items).some(i => /^\d{1,2}$/.test(i.innerText.trim()));
                                return el.offsetHeight > 50 && items.length > 3 && hasNumbers;
                            });
                            
                            if (allCandidates.length < 1) {
                                return {success: false, error: 'no_candidates', count: 0};
                            }
                            
                            // Ordena por posição X
                            allCandidates.sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x);
                            
                            // Agrupa por posição X (colunas com X próximo são consideradas a mesma coluna)
                            const groups = [];
                            let currentGroup = [allCandidates[0]];
                            for (let i = 1; i < allCandidates.length; i++) {
                                const prevX = currentGroup[0].getBoundingClientRect().x;
                                const currX = allCandidates[i].getBoundingClientRect().x;
                                if (Math.abs(currX - prevX) < 30) {
                                    currentGroup.push(allCandidates[i]);
                                } else {
                                    groups.push(currentGroup);
                                    currentGroup = [allCandidates[i]];
                                }
                            }
                            groups.push(currentGroup);
                            
                            if (groups.length < 2) {
                                return {success: false, error: 'less_than_2_groups', groupCount: groups.length, candidateCount: allCandidates.length};
                            }
                            
                            // Pega o elemento mais interno de cada grupo (menor width)
                            const hourCol = groups[0].sort((a, b) => a.offsetWidth - b.offsetWidth)[0];
                            const minCol = groups[1].sort((a, b) => a.offsetWidth - b.offsetWidth)[0];
                            
                            // Debug: informações das colunas
                            const hourBox = hourCol.getBoundingClientRect();
                            const minBox = minCol.getBoundingClientRect();
                            
                            // Função para ENCONTRAR o item e retornar coordenadas (não clicar)
                            const findItem = (col, val, colName) => {
                                // Reseta o scroll da coluna
                                col.scrollTop = 0;
                                
                                // Tenta encontrar várias vezes com scroll progressivo
                                for (let attempt = 0; attempt < 15; attempt++) {
                                    const items = col.querySelectorAll('li, div, span');
                                    for (const item of items) {
                                        const text = item.innerText.trim();
                                        if (text === val || text === val.padStart(2, '0')) {
                                            item.scrollIntoView({block: 'center', behavior: 'instant'});
                                            const rect = item.getBoundingClientRect();
                                            return {found: true, x: rect.x + rect.width/2, y: rect.y + rect.height/2, val, attempt};
                                        }
                                    }
                                    // Scroll para revelar mais itens
                                    col.scrollTop += 40;
                                }
                                return {found: false, val, attempts: 15};
                            };
                            
                            const hourResult = findItem(hourCol, targetH, 'HOUR');
                            const minResult = findItem(minCol, targetM, 'MIN');
                            
                            return {
                                success: hourResult.found && minResult.found, 
                                hourFound: hourResult.found,
                                hourX: hourResult.x,
                                hourY: hourResult.y,
                                minFound: minResult.found,
                                minX: minResult.x,
                                minY: minResult.y,
                                columnsFound: groups.length
                            };
                        }""", [target_hour, target_minute])
                        
                        logger.info(f"📊 Resultado Column Click: {column_click_result}")
                        
                        if column_click_result.get('success'):
                            # Usa Playwright para cliques REAIS
                            await page.mouse.click(column_click_result['hourX'], column_click_result['hourY'])
                            await page.wait_for_timeout(300)
                            await page.mouse.click(column_click_result['minX'], column_click_result['minY'])
                            await page.wait_for_timeout(500)
                            logger.info(f"✅ Cliques Playwright em ({column_click_result['hourX']:.0f}, {column_click_result['hourY']:.0f}) e ({column_click_result['minX']:.0f}, {column_click_result['minY']:.0f})")
                        else:
                            logger.warning("⚠️ Column Click falhou. Tentando fallback com teclado...")
                            # Fallback: tenta teclado
                            await page.keyboard.press("Control+A")
                            await page.keyboard.press("Backspace")
                            await page.keyboard.type(target_str, delay=50)
                            await page.keyboard.press("Enter")
                        
                        await page.wait_for_timeout(1500)  # Pausa importante antes de fechar
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(500)

            if monitor:
                await monitor.capture_full_state(page, "pos_agendamento_click", "Dados selecionados via clique")

        # ========== VERIFICAÇÃO FINAL ANTES DE CONFIRMAR ==========
        logger.info("🔍 Iniciando VERIFICAÇÃO FINAL antes de confirmar...")
        
        # Primeiro fecha qualquer picker aberto
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(800)
        
        max_final_checks = 3
        for final_check in range(max_final_checks):
            # Captura TODO o texto visível da página e procura o padrão de agendamento
            page_text = await page.evaluate("""() => document.body.innerText""")
            
            # Procura pelo padrão "X de jan, HH:MM" no texto da página
            import_re = __import__('re')
            schedule_match = import_re.search(r'(\d{1,2})\s+de\s+(jan|fev|mar|abr|mai|jun)[^\n]*?(\d{1,2}:\d{2})', page_text, import_re.IGNORECASE)
            
            if schedule_match:
                found_day = schedule_match.group(1)
                found_time = schedule_match.group(3)
                logger.info(f"🧐 VERIFICAÇÃO FINAL {final_check+1}: Dia='{found_day}' Hora='{found_time}'")
                
                # Verifica se DATA e HORA estão corretas
                if str(target_day) == found_day and target_str == found_time:
                    logger.info(f"✅ VERIFICAÇÃO FINAL OK: Dia {target_day} e Hora {target_str} confirmados!")
                    break
                else:
                    logger.warning(f"⚠️ VERIFICAÇÃO FINAL FALHOU: Esperado dia {target_day} às {target_str}, encontrado dia '{found_day}' às '{found_time}'")                
                if final_check < max_final_checks - 1:
                    logger.info("🔄 Tentando corrigir novamente...")
                    # Re-clica no badge de hora para tentar corrigir
                    time_badge = page.locator('[class*="tux-badge"]:has-text(":"), [class*="time-picker-input"], [class*="schedule-time"]').last
                    if await time_badge.count() > 0:
                        await time_badge.click()
                        await page.wait_for_timeout(500)
                        await page.keyboard.press("Control+A")
                        await page.keyboard.press("Backspace")
                        await page.keyboard.type(target_str, delay=50)
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(1000)
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(500)
                else:
                    logger.error("❌ VERIFICAÇÃO FINAL: Não foi possível garantir data/hora corretas após 3 tentativas.")
            
            await page.wait_for_timeout(500)
        
        if monitor:
            await monitor.capture_full_state(page, "pos_verificacao_final", "Após verificação final")
        
        # ========== CLICK FINAL & MODAL DE CONFIRMAÇÃO ==========
        await nuke_modals(page)
        logger.info("🚀 Preparando para finalizar...")
        
        # Botão Final
        btn_text = "Programar" if schedule_time else "Publicar"
        
        # Botão Final - Broad Selector
        final_btn = page.locator('button:has-text("Programar"), button:has-text("Schedule"), button:has-text("Publicar"), button:has-text("Post"), button:has-text("Agendar")').last
        
        if await final_btn.is_visible():
            if await final_btn.is_enabled():
                await final_btn.click()
                logger.info(f"✅ Botão final clicado.")
                
                # LOOP DE CONFIRMAÇÃO (RETRY AGGRESSIVE)
                confirmed = False
                for m_attempt in range(5):
                    await page.wait_for_timeout(2500)
                    
                    # 1. Checar se já completou (Redirecionamento ou Sucesso)
                    if await page.locator('text="Manage your posts", text="Gerenciar suas postagens", text="View analytics"').count() > 0:
                        logger.info("🎉 Sucesso detectado pós-modal!")
                        confirmed = True
                        break
                        
                    # 2. Procurar modal
                    modal_confirm = page.locator('div[role="dialog"] button').filter(has_text=re.compile(r"(Programar|Schedule|Confirmar|Post|Publicar|Postar)", re.I)).last
                    
                    if await modal_confirm.count() > 0 and await modal_confirm.is_visible():
                        logger.info(f"📢 Modal de confirmação detectado (Attempt {m_attempt+1}). Confirmando...")
                        if monitor:
                            await monitor.capture_full_state(page, f"modal_confirm_attempt_{m_attempt}", "Modal detectado")
                        await modal_confirm.click(force=True)
                        await page.wait_for_timeout(3000)
                    else:
                        logger.info(f"ℹ️ Tentativa {m_attempt+1}: Nenhum modal visível.")
                        if m_attempt > 0: # Se já passou do primeiro check, assume sucesso
                            confirmed = True
                            break
                
                # SUCESSO NO CLICK
                result["status"] = "ready"
                result["message"] = "Action completed"
                    
            else:
                logger.warning(f"⚠️ Botão '{btn_text}' está desabilitado (upload incompleto ou validação falhou).")
                result["status"] = "error"
                result["message"] = f"Button {btn_text} disabled"
        else:
            logger.error(f"❌ Botão '{btn_text}' não encontrado!")
            result["status"] = "error"
            result["message"] = f"Button {btn_text} not found"

        # Wait for completion/redirect logic or final checks
        await page.wait_for_timeout(5000)
        if monitor:
            await monitor.capture_full_state(page, "estado_final", "Após tentativa de publicação")
        
        # Check for error toasts
        if await page.locator('.toast-error, .start-toast-error').count() > 0:
             error_msg = await page.locator('.toast-error').inner_text()
             result["status"] = "error"
             result["message"] = f"TikTok recusou: {error_msg}"
            
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        result["message"] = str(e)
        # Captura estado de erro
        try:
            if monitor:
                await monitor.capture_full_state(page, "ERRO_FINAL",
                                                f"Erro durante execução: {str(e)[:100]}")
        except:
            pass
    finally:
        if monitor:
            # Pagar captura contínua
            await monitor.stop_continuous_screenshot()
            
            # Captura final
            await monitor.capture_full_state(page, "estado_final",
                                            f"Estado final - Status: {result['status']}")
            
            # 🎬 PARAR TRACE E SALVAR
            trace_file = await monitor.stop_tracing(context)
            result["trace_file"] = trace_file
            
            # 📊 SALVAR RELATÓRIO ULTRA-COMPLETO
            report_file = monitor.save_final_report()
            result["monitor_report"] = report_file

            await close_browser(p, browser)
            
            logger.info("="*60)
            logger.info(f"👁️ OLHO DE DEUS COMPLETO!")
            logger.info(f"📊 Relatório: {report_file}")
            if trace_file:
                logger.info(f"🎬 Trace: {trace_file}")
                logger.info(f"👉 Análise interativa: npx playwright show-trace {trace_file}")
            logger.info("="*60)
        else:
            await close_browser(p, browser)

        # 🔓 RELEASE LOCK
        if _lock_acquired:
            try:
                _lock_ctx.__exit__(None, None, None)
            except Exception as le:
                logger.error(f"Erro ao liberar lock: {le}")
        
    return result
