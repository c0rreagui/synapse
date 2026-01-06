"""
TikTok Uploader Module - VERSÃO ULTRA-MONITORADA 👁️
Captura TODAS as informações possíveis do Bot e TikTok Studio
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

logger = logging.getLogger(__name__)

async def upload_video_monitored(
    session_name: str,
    video_path: str,
    caption: str,
    hashtags: list = None,
    schedule_time: str = None, 
    post: bool = False
) -> dict:
    result = {"status": "error", "message": "", "screenshot_path": None}
    
    # 👁️ ATIVAR MONITOR ULTRA-DETALHADO
    monitor = TikTokMonitor(session_name)
    logger.info(f"👁️ OLHO QUE TUDO VÊ ativado: {monitor.run_id}")

    if not os.path.exists(video_path):
        return {"status": "error", "message": "Video not found"}
    
    session_path = get_session_path(session_name)
    p, browser, context, page = await launch_browser(headless=False, storage_state=session_path)
    
    # 🎬 INICIAR PLAYWRIGHT TRACE (captura TUDO automaticamente)
    await monitor.start_tracing(context)
    
    # 📝 Injetar console logger ULTRA-DETALHADO
    await monitor.inject_console_logger(page)
    
    # 📸 INICIAR CAPTURA CONTÍNUA (500ms)
    await monitor.start_continuous_screenshot(page, interval=0.5)
    
    try:
        # ========== STEP 1: NAVEGAÇÃO ==========
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=120000)
        await page.wait_for_timeout(5000)
        await monitor.capture_full_state(page, "navegacao_inicial", 
                                        "Página de upload do TikTok Studio carregada")
        
        # ========== STEP 2: UPLOAD DO VÍDEO ==========
        file_input = await page.wait_for_selector('input[type="file"]', timeout=15000, state="attached")
        await file_input.set_input_files(video_path)
        logger.info("📤 Upload do arquivo iniciad o...")
        await page.wait_for_timeout(2000)
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
        await monitor.capture_full_state(page, "pos_dom_nuker",
                                        "DOM Nuker executado - Overlays e tutoriais removidos")

        # ========== PREENCHIMENTO DA LEGENDA (FOCO ALVO) ==========
        full_caption = f"{caption} " + " ".join([f"#{h}" for h in hashtags]) if hashtags else caption
        
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
            await monitor.capture_full_state(page, "aviso_upload_timeout", "Timeout esperando upload")

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
                                'ul, [role="listbox"], [class*="column"], [class*="picker"], [class*="list"], [class*="scroll"], [class*="time"]'
                            )).filter(el => {
                                const items = el.querySelectorAll('li, div, span');
                                const hasNumbers = Array.from(items).some(i => /^\d{1,2}$/.test(i.innerText.trim()));
                                return el.offsetHeight > 50 && items.length > 3 && hasNumbers;
                            });
                            
                            // Filtra para remover elementos aninhados (pega apenas os de nível mais externo)
                            let columns = allCandidates.filter(col => {
                                return !allCandidates.some(other => other !== col && other.contains(col));
                            });
                            
                            // Debug: conta todos os elementos candidatos
                            if (columns.length < 2) {
                                return {success: false, error: 'less_than_2_columns', count: columns.length, candidateCount: allCandidates.length};
                            }
                            
                            // Ordena por posição X (esquerda para direita)
                            columns.sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x);
                            
                            // Pega as duas primeiras colunas com posições X distintas (pelo menos 30px de diferença)
                            let hourCol = columns[0];
                            let minCol = null;
                            for (let i = 1; i < columns.length; i++) {
                                if (columns[i].getBoundingClientRect().x - hourCol.getBoundingClientRect().x > 30) {
                                    minCol = columns[i];
                                    break;
                                }
                            }
                            if (!minCol) minCol = columns[1] || columns[0];
                            
                            // Debug: informações das colunas
                            const hourBox = hourCol.getBoundingClientRect();
                            const minBox = minCol.getBoundingClientRect();
                            
                            // Função para clicar no item correto (com scroll para virtualizados)
                            const clickItem = (col, val, colName) => {
                                // Reseta o scroll da coluna
                                col.scrollTop = 0;
                                
                                // Tenta encontrar e clicar várias vezes com scroll progressivo
                                for (let attempt = 0; attempt < 15; attempt++) {
                                    const items = col.querySelectorAll('li, div, span');
                                    for (const item of items) {
                                        const text = item.innerText.trim();
                                        if (text === val || text === val.padStart(2, '0')) {
                                            // Clica diretamente no elemento
                                            item.scrollIntoView({block: 'center', behavior: 'instant'});
                                            item.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                                            item.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                                            item.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                                            return {success: true, val, attempt};
                                        }
                                    }
                                    // Scroll para revelar mais itens
                                    col.scrollTop += 40;
                                }
                                return {success: false, val, attempts: 15};
                            };
                            
                            const hourResult = clickItem(hourCol, targetH, 'HOUR');
                            const minResult = clickItem(minCol, targetM, 'MIN');
                            
                            return {
                                success: hourResult.success && minResult.success, 
                                hourClicked: hourResult.success, 
                                minClicked: minResult.success,
                                hourBox: {x: hourBox.x, y: hourBox.y, w: hourBox.width},
                                minBox: {x: minBox.x, y: minBox.y, w: minBox.width},
                                columnsFound: columns.length
                            };
                        }""", [target_hour, target_minute])
                        
                        logger.info(f"📊 Resultado Column Click: {column_click_result}")
                        
                        if not column_click_result.get('success'):
                            logger.warning("⚠️ Column Click falhou. Tentando fallback com teclado...")
                            # Fallback: tenta teclado
                            await page.keyboard.press("Control+A")
                            await page.keyboard.press("Backspace")
                            await page.keyboard.type(target_str, delay=50)
                            await page.keyboard.press("Enter")
                        
                        await page.wait_for_timeout(1500)  # Pausa importante antes de fechar
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(500)

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
        
        await monitor.capture_full_state(page, "pos_verificacao_final", "Após verificação final")
        
        # ========== CLICK FINAL & MODAL DE CONFIRMAÇÃO ==========
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
            await monitor.capture_full_state(page, "ERRO_FINAL",
                                            f"Erro durante execução: {str(e)[:100]}")
        except:
            pass
    finally:
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
        logger.info(f"👁️ MONITORAMENTO COMPLETO!")
        logger.info(f"📊 Relatório: {report_file}")
        if trace_file:
            logger.info(f"🎬 Trace: {trace_file}")
            logger.info(f"👉 Análise interativa: npx playwright show-trace {trace_file}")
        logger.info("="*60)
        
    return result
