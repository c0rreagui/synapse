"""
👁️ OLHO QUE TUDO VÊ - Sistema de Monitoramento ULTRA-COMPLETO
Captura ABSOLUTAMENTE TODAS as informações possíveis do TikTok Studio e Bot
"""
import asyncio
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class TikTokMonitor:
    """Monitor ULTRA-DETALHADO - Captura TUDO do TikTok Studio"""
    
    def __init__(self, session_name: str, base_dir: str = "MONITOR"):
        self.session_name = session_name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{session_name}_{timestamp}"
        
        # 📁 ESTRUTURA ORGANIZADA DO MONITOR
        # MONITOR/
        #   ├── runs/                    (todas as execuções)
        #   │   └── {session}_{timestamp}/
        #   │       ├── 01_capturas/     (screenshots, videos)
        #   │       ├── 02_codigo/       (html, dom, scripts, css)
        #   │       ├── 03_dados/        (cookies, storage, globals)
        #   │       ├── 04_debug/        (console, performance)
        #   │       └── 05_traces/       (playwright trace)
        #   └── index.md                 (índice de todas as runs)
        
        # Diretório principal do monitor
        monitor_root = Path(base_dir)
        monitor_root.mkdir(exist_ok=True)
        
        # Diretório desta execução específica
        self.base_path = monitor_root / "runs" / self.run_id
        
        # === SUBPASTAS ORGANIZADAS ===
        # 01 - CAPTURAS VISUAIS
        self.capturas_path = self.base_path / "01_capturas"
        self.screenshots_path = self.capturas_path / "screenshots"
        self.videos_path = self.capturas_path / "videos"
        
        # 02 - CÓDIGO & ESTRUTURA
        self.codigo_path = self.base_path / "02_codigo"
        self.html_path = self.codigo_path / "html"
        self.dom_path = self.codigo_path / "dom"
        self.scripts_path = self.codigo_path / "scripts"
        self.css_path = self.codigo_path / "css"
        self.accessibility_path = self.codigo_path / "accessibility"
        
        # 03 - DADOS & STATE
        self.dados_path = self.base_path / "03_dados"
        self.cookies_path = self.dados_path / "cookies"
        self.storage_path = self.dados_path / "storage"
        self.globals_path = self.dados_path / "globals"
        
        # 04 - DEBUG & PERFORMANCE
        self.debug_path = self.base_path / "04_debug"
        self.console_path = self.debug_path / "console"
        self.metrics_path = self.debug_path / "performance"
        self.network_path = self.debug_path / "network"
        self.events_path = self.debug_path / "events"
        
        # 05 - TRACES & REPLAYS
        self.traces_path = self.base_path / "05_traces"
        
        # Criar TODA a estrutura organizada
        for path in [self.capturas_path, self.codigo_path, self.dados_path, 
                     self.debug_path, self.traces_path,
                     self.screenshots_path, self.videos_path,
                     self.html_path, self.dom_path, self.scripts_path, 
                     self.css_path, self.accessibility_path,
                     self.cookies_path, self.storage_path, self.globals_path,
                     self.console_path, self.metrics_path, self.network_path, 
                     self.events_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Métricas expandidas
        self.step_counter = 0
        self.metrics = {
            "start_time": timestamp,
            "run_id": self.run_id,
            "session_name": session_name,
            "steps": [],
            "errors": [],
            "network_requests": [],
            "console_logs": [],
            "performance_metrics": [],
            "playwright_actions": []
        }
        
        logger.info(f"👁️ OLHO QUE TUDO VÊ ativado: {self.run_id}")
        logger.info(f"📁 Pasta: MONITOR/runs/{self.run_id}/")
    
    async def start_continuous_screenshot(self, page, interval: float = 0.5):
        """Inicia captura contínua de screenshots em background (500ms)"""
        if hasattr(self, "_screenshot_task") and self._screenshot_task:
            return
        
        self._stop_screenshot = False
        
        async def _loop():
            counter = 0
            while not self._stop_screenshot:
                try:
                    if page.is_closed(): break
                    timestamp = datetime.now().strftime("%H%M%S_%f")[:9]
                    filename = f"c_{counter:04d}_{timestamp}.jpg"
                    path = self.screenshots_path / "continuous" / filename
                    path.parent.mkdir(exist_ok=True)
                    # Qualidade reduzida para evitar gargalo de IO
                    await page.screenshot(path=str(path), type="jpeg", quality=40)
                    counter += 1
                except Exception:
                    pass
                await asyncio.sleep(interval)
                
        self._screenshot_task = asyncio.create_task(_loop())
        logger.info(f"📸 Captura contínua iniciada ({interval}s)")

    async def stop_continuous_screenshot(self):
        """Para a captura contínua"""
        self._stop_screenshot = True
        if hasattr(self, "_screenshot_task") and self._screenshot_task:
            try:
                await self._screenshot_task
            except: pass
            self._screenshot_task = None
        logger.info("📸 Captura contínua finalizada")

    async def capture_full_state(self, page, step_name: str, description: str = ""):
        """Captura ABSOLUTAMENTE TUDO do estado atual"""
        self.step_counter += 1
        step_id = f"{self.step_counter:03d}_{step_name}"
        
        step_data = {
            "step_id": step_id,
            "name": step_name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "artifacts": {},
            "metadata": {}
        }
        
        try:
            # ========== CAPTURAS VISUAIS ==========
            
            # 1️⃣ SCREENSHOT (página inteira)
            screenshot_file = self.screenshots_path / f"{step_id}_full.png"
            await page.screenshot(path=str(screenshot_file), full_page=True)
            step_data["artifacts"]["screenshot_full"] = str(screenshot_file)
            
            # 📸 SCREENSHOT (viewport)
            await page.screenshot(path=str(screenshot_viewport))
            step_data["artifacts"]["screenshot_viewport"] = str(screenshot_viewport)
            
            # 🖼️ LIVE VIEW UPDATE
            try:
                static_dir = self.base_path.parent.parent.parent / "backend" / "static"
                if static_dir.exists():
                    latest_path = static_dir / "monitor_live.jpg"
                    import shutil
                    shutil.copy(screenshot_viewport, latest_path)
            except Exception as e:
                logger.warning(f"Falha ao atualizar Live View: {e}")
            
            # ========== HTML & DOM ==========
            
            # 2️⃣ HTML COMPLETO
            html_content = await page.content()
            html_file = self.html_path / f"{step_id}.html"
            html_file.write_text(html_content, encoding='utf-8')
            step_data["artifacts"]["html"] = str(html_file)
            
            # 3️⃣ ESTRUTURA DOM ULTRA-DETALHADA
            dom_structure = await page.evaluate("""
                () => {
                    const getElementInfo = (el) => {
                        const rect = el.getBoundingClientRect();
                        const computed = window.getComputedStyle(el);
                        
                        return {
                            tag: el.tagName,
                            id: el.id || null,
                            classes: Array.from(el.classList),
                            attributes: Object.fromEntries(
                                Array.from(el.attributes).map(attr => [attr.name, attr.value])
                            ),
                            text: el.innerText?.substring(0, 200) || null,
                            value: el.value || null,
                            visible: !!(el.offsetWidth || el.offsetHeight),
                            position: {x: rect.x, y: rect.y, width: rect.width, height: rect.height},
                            computedStyle: {
                                display: computed.display,
                                visibility: computed.visibility,
                                opacity: computed.opacity,
                                zIndex: computed.zIndex,
                                position: computed.position,
                                pointerEvents: computed.pointerEvents,
                                backgroundColor: computed.backgroundColor,
                                color: computed.color
                            },
                            eventListeners: window.getEventListeners ? 
                                Object.keys(window.getEventListeners(el) || {}) : []
                        };
                    };
                    
                    return {
                        title: document.title,
                        url: window.location.href,
                        readyState: document.readyState,
                        // TODOS os botões
                        buttons: Array.from(document.querySelectorAll('button')).map(getElementInfo),
                        // TODOS os inputs
                        inputs: Array.from(document.querySelectorAll('input, textarea')).map(getElementInfo),
                        // TODOS os links
                        links: Array.from(document.querySelectorAll('a')).map(getElementInfo),
                        // TODOS os modais/dialogs
                        modals: Array.from(document.querySelectorAll('[role="dialog"], .modal, [class*="modal"], dialog')).map(getElementInfo),
                        // TODOS os overlays
                        overlays: Array.from(document.querySelectorAll('[class*="overlay"], [data-test-id="overlay"], [class*="mask"]')).map(getElementInfo),
                        // TODOS os elementos de tutorial
                        tutorials: Array.from(document.querySelectorAll('[class*="tutorial"], [class*="guide"], [class*="joyride"], [class*="tooltip"]')).map(getElementInfo),
                        // Elementos com alto z-index (provavelmente overlays)
                        highZIndex: Array.from(document.querySelectorAll('*')).filter(el => {
                            const z = parseInt(window.getComputedStyle(el).zIndex);
                            return z > 1000;
                        }).map(getElementInfo),
                        // Elementos com position fixed/absolute
                        positioned: Array.from(document.querySelectorAll('*')).filter(el => {
                            const pos = window.getComputedStyle(el).position;
                            return pos === 'fixed' || pos === 'absolute';
                        }).slice(0, 50).map(getElementInfo),
                        // Iframes
                        iframes: Array.from(document.querySelectorAll('iframe')).map(getElementInfo)
                    };
                }
            """)
            dom_file = self.dom_path / f"{step_id}.json"
            dom_file.write_text(json.dumps(dom_structure, indent=2, ensure_ascii=False), encoding='utf-8')
            step_data["artifacts"]["dom"] = str(dom_file)
            
            # ========== STORAGE & COOKIES ==========
            
            # 4️⃣ COOKIES
            cookies = await page.context.cookies()
            cookies_file = self.cookies_path / f"{step_id}.json"
            cookies_file.write_text(json.dumps(cookies, indent=2), encoding='utf-8')
            step_data["artifacts"]["cookies"] = str(cookies_file)
            
            # 5️⃣ LOCAL STORAGE
            local_storage = await page.evaluate("() => Object.fromEntries(Object.entries(localStorage))")
            storage_file = self.storage_path / f"{step_id}_local.json"
            storage_file.write_text(json.dumps(local_storage, indent=2, ensure_ascii=False), encoding='utf-8')
            step_data["artifacts"]["localStorage"] = str(storage_file)
            
            # 6️⃣ SESSION STORAGE
            session_storage = await page.evaluate("() => Object.fromEntries(Object.entries(sessionStorage))")
            session_file = self.storage_path / f"{step_id}_session.json"
            session_file.write_text(json.dumps(session_storage, indent=2, ensure_ascii=False), encoding='utf-8')
            step_data["artifacts"]["sessionStorage"] = str(session_file)
            
            # ========== JAVASCRIPT INTERNALS ==========
            
            # 7️⃣ VARIÁVEIS GLOBAIS DO WINDOW
            globals_data = await page.evaluate("""
                () => {
                    const result = {};
                    
                    // Captura variáveis TikTok específicas
                    const tiktokKeys = Object.keys(window).filter(k => 
                        k.toLowerCase().includes('tiktok') || 
                        k.toLowerCase().includes('tt') ||
                        k.toLowerCase().includes('studio') ||
                        k.toLowerCase().includes('upload')
                    );
                    
                    tiktokKeys.forEach(key => {
                        try {
                            const value = window[key];
                            if (typeof value === 'object' && value !== null) {
                                result[key] = JSON.parse(JSON.stringify(value, null, 2));
                            } else {
                                result[key] = String(value);
                            }
                        } catch(e) {
                            result[key] = `[Error: ${e.message}]`;
                        }
                    });
                    
                    // Captura configurações globais
                    result['__CONFIG'] = {
                        userAgent: navigator.userAgent,
                        language: navigator.language,
                        platform: navigator.platform,
                        cookieEnabled: navigator.cookieEnabled,
                        onLine: navigator.onLine,
                        screenWidth: window.screen.width,
                        screenHeight: window.screen.height,
                        innerWidth: window.innerWidth,
                        innerHeight: window.innerHeight
                    };
                    
                    return result;
                }
            """)
            globals_file = self.globals_path / f"{step_id}.json"
            globals_file.write_text(json.dumps(globals_data, indent=2, ensure_ascii=False), encoding='utf-8')
            step_data["artifacts"]["globals"] = str(globals_file)
            
            # ========== CONSOLE & NETWORK ==========
            
            # 8️⃣ CONSOLE LOGS
            console_logs = await page.evaluate("() => window.__consoleLogs || []")
            console_file = self.console_path / f"{step_id}.json"
            console_file.write_text(json.dumps(console_logs, indent=2), encoding='utf-8')
            step_data["artifacts"]["console"] = str(console_file)
            
            # ========== CSS & SCRIPTS ==========
            
            # 9️⃣ TODOS OS SCRIPTS CARREGADOS
            scripts = await page.evaluate("""
                () => Array.from(document.querySelectorAll('script')).map(s => ({
                    src: s.src || null,
                    type: s.type || null,
                    async: s.async,
                    defer: s.defer,
                    innerHTML: s.innerHTML ? s.innerHTML.substring(0, 500) : null
                }))
            """)
            scripts_file = self.scripts_path / f"{step_id}.json"
            scripts_file.write_text(json.dumps(scripts, indent=2), encoding='utf-8')
            step_data["artifacts"]["scripts"] = str(scripts_file)
            
            # 🔟 TODAS AS FOLHAS DE ESTILO
            stylesheets = await page.evaluate("""
                () => Array.from(document.styleSheets).map(sheet => {
                    try {
                        return {
                            href: sheet.href,
                            disabled: sheet.disabled,
                            rulesCount: sheet.cssRules ? sheet.cssRules.length : 0
                        };
                    } catch(e) {
                        return {href: sheet.href, error: 'CORS blocked'};
                    }
                })
            """)
            css_file = self.css_path / f"{step_id}.json"
            css_file.write_text(json.dumps(stylesheets, indent=2), encoding='utf-8')
            step_data["artifacts"]["css"] = str(css_file)
            
            # ========== PERFORMANCE ==========
            
            # 1️⃣1️⃣ PERFORMANCE METRICS
            performance = await page.evaluate("""
                () => {
                    const perf = window.performance;
                    const timing = perf.timing;
                    
                    return {
                        navigation: {
                            loadStart: timing.loadEventStart - timing.navigationStart,
                            domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
                            loadComplete: timing.loadEventEnd - timing.navigationStart
                        },
                        resources: perf.getEntriesByType('resource').map(r => ({
                            name: r.name,
                            duration: r.duration,
                            size: r.transferSize,
                            type: r.initiatorType
                        })),
                        memory: performance.memory ? {
                            usedJSHeapSize: performance.memory.usedJSHeapSize,
                            totalJSHeapSize: performance.memory.totalJSHeapSize,
                            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                        } : null
                    };
                }
            """)
            perf_file = self.metrics_path / f"{step_id}.json"
            perf_file.write_text(json.dumps(performance, indent=2), encoding='utf-8')
            step_data["artifacts"]["performance"] = str(perf_file)
            
            # ========== ACCESSIBILITY ==========
            
            # 1️⃣2️⃣ ACCESSIBILITY TREE SNAPSHOT
            try:
                accessibility_tree = await page.accessibility.snapshot()
                acc_file = self.accessibility_path / f"{step_id}.json"
                acc_file.write_text(json.dumps(accessibility_tree, indent=2), encoding='utf-8')
                step_data["artifacts"]["accessibility"] = str(acc_file)
            except Exception as e:
                logger.warning(f"Não conseguiu capturar accessibility tree: {e}")
            
            # ========== METADATA ==========
            
            step_data["metadata"] = {
                "viewport": page.viewport_size,
                "url": page.url,
                "title": await page.title()
            }
            
            logger.info(f"👁️ Captura ULTRA-COMPLETA: {step_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro na captura: {e}", exc_info=True)
            step_data["error"] = str(e)
        
        self.metrics["steps"].append(step_data)
        return step_data
    
    async def inject_console_logger(self, page):
        """Injeta logger ULTRA-DETALHADO de console"""
        await page.evaluate("""
            () => {
                if (!window.__consoleLogs) {
                    window.__consoleLogs = [];
                    
                    const createLogger = (type, original) => {
                        return function(...args) {
                            window.__consoleLogs.push({
                                type: type,
                                time: new Date().toISOString(),
                                args: args.map(arg => {
                                    try {
                                        return JSON.stringify(arg);
                                    } catch(e) {
                                        return String(arg);
                                    }
                                }),
                                stack: new Error().stack
                            });
                            original.apply(console, args);
                        };
                    };
                    
                    console.log = createLogger('log', console.log);
                    console.warn = createLogger('warn', console.warn);
                    console.error = createLogger('error', console.error);
                    console.info = createLogger('info', console.info);
                    console.debug = createLogger('debug', console.debug);
                    
                    // Captura erros não tratados
                    window.addEventListener('error', (e) => {
                        window.__consoleLogs.push({
                            type: 'uncaughtError',
                            time: new Date().toISOString(),
                            message: e.message,
                            filename: e.filename,
                            lineno: e.lineno,
                            colno: e.colno,
                            stack: e.error ? e.error.stack : null
                        });
                    });
                    
                    // Captura promises rejeitadas
                    window.addEventListener('unhandledrejection', (e) => {
                        window.__consoleLogs.push({
                            type: 'unhandledRejection',
                            time: new Date().toISOString(),
                            reason: String(e.reason),
                            promise: String(e.promise)
                        });
                    });
                }
            }
        """)
    
    async def start_tracing(self, context):
        """Inicia Playwright trace (gravação completa)"""
        try:
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            logger.info("📹 Playwright tracing iniciado")
        except Exception as e:
            logger.warning(f"Não conseguiu iniciar tracing: {e}")
    
    async def stop_tracing(self, context):
        """Para e salva Playwright trace"""
        try:
            trace_file = self.traces_path / f"{self.run_id}_trace.zip"
            await context.tracing.stop(path=str(trace_file))
            logger.info(f"📹 Trace salvo: {trace_file}")
            return str(trace_file)
        except Exception as e:
            logger.warning(f"Não conseguiu salvar trace: {e}")
            return None
    
    async def start_video_recording(self, context):
        """Inicia gravação de vídeo do navegador"""
        # O vídeo é configurado no launch do browser
        logger.info("🎥 Gravação de vídeo ativa")
    
    def save_final_report(self):
        """Salva relatório ULTRA-COMPLETO"""
        self.metrics["end_time"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics["total_steps"] = self.step_counter
        
        report_file = self.base_path / "REPORT.json"
        report_file.write_text(json.dumps(self.metrics, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # README super detalhado
        readme = f"""# 👁️ OLHO QUE TUDO VÊ - Relatório ULTRA-COMPLETO

## Informações da Sessão
- **Run ID**: {self.run_id}
- **Sessão**: {self.session_name}
- **Início**: {self.metrics['start_time']}
- **Fim**: {self.metrics.get('end_time', 'Em progresso')}
- **Total de Etapas**: {self.step_counter}

## 📁 Estrutura de Diretórios Organizads

### 01_capturas/
- `screenshots/` - Screenshots completos (full page + viewport)
- `videos/` - Gravações em vídeo da sessão

### 02_codigo/
- `html/` - HTML completo de cada step
- `dom/` - Estrutura DOM ultra-detalhada
- `scripts/` - Scripts carregados
- `css/` - Folhas de estilo
- `accessibility/` - Árvore de acessibilidade

### 03_dados/
- `cookies/` - Cookies de autenticação
- `storage/` - LocalStorage e SessionStorage
- `globals/` - Variáveis globais (TikTok internals)

### 04_debug/
- `console/` - Logs do console (erros, warnings)
- `performance/` - Métricas de performance
- `network/` - Logs de rede
- `events/` - Listeners de eventos

### 05_traces/
- `{self.run_id}_trace.zip` - Playwright TRACE (Use: `npx playwright show-trace`)

### Relatórios
- `REPORT.json` - Dados brutos em JSON
- `README.md` - Este arquivo

## 🔍 Como Analisar

### 1. Análise Visual
1. Veja `01_capturas/screenshots` em ordem numérica
2. Trace: `npx playwright show-trace 05_traces/{self.run_id}_trace.zip`

### 2. Análise de Bloqueios (Overlays/Tutoriais)
1. Abra `02_codigo/dom/XXX_<step>.json`
2. Procure por chaves: `overlays`, `modals`, `tutorials`

### 3. Análise de Erros
1. Veja `04_debug/console/` para logs de erro
2. Veja `01_capturas/screenshots` para erros visuais

### 4. Análise de Estado
1. `03_dados/globals/` para ver variáveis internas do TikTok
2. `03_dados/cookies/` para sessão

## 📊 Etapas Capturadas
"""
        
        for step in self.metrics["steps"]:
            readme += f"\n### {step['step_id']}: {step['name']}\n"
            if step.get('description'):
                readme += f"**Descrição**: {step['description']}\n\n"
            if step.get('metadata'):
                readme += f"**URL**: {step['metadata'].get('url', 'N/A')}\n\n"
            if step.get('error'):
                readme += f"⚠️ **ERRO**: {step['error']}\n\n"
        
        readme += f"\n## 🎯 Comandos Úteis\n\n"
        readme += f"```bash\n"
        readme += f"# Visualizar Trace Interativo (RECOMENDADO)\n"
        readme += f"npx playwright show-trace 05_traces/{self.run_id}_trace.zip\n"
        readme += f"```\n"
        
        readme_file = self.base_path / "README.md"
        readme_file.write_text(readme, encoding='utf-8')
        
        logger.info(f"📊 Relatório ULTRA-COMPLETO salvo: {report_file}")
        logger.info(f"👉 Para análise interativa: npx playwright show-trace {self.traces_path}/{self.run_id}_trace.zip")
        
        return str(report_file)
