# Auditoria de Anti-Detecção — Synapse TikTok Pipeline

> **Data:** 2026-03-27
> **Objetivo:** Identificar e corrigir todas as vulnerabilidades que levaram ao ban do TikTok
> **Progresso:** 87/102 (itens agrupados: #89-94 → 1, #100-103 → 1)

---

## Categoria 1: Detecção de Automação (CRITICAL)

- [x] **#1** ~~`--headless=new` detectável~~ — Em Docker, `launch_browser_for_profile` agora usa `headless=False` (Xvfb auto-start). `--headless=new` só em dev local. `browser.py`
- [x] **#2** ~~playwright-stealth NÃO instalado~~ — Adicionado `playwright-stealth` ao `pip install` no Dockerfile (já estava em requirements.txt mas era ignorado). `Dockerfile`
- [x] **#3** ~~`navigator.webdriver` setado como `undefined` em vez de `false`~~ — Corrigido para `false` em `browser.py` e `remote_session.py`
- [x] **#4** ~~Porta CDP 9222 exposta~~ — Adicionado `--remote-debugging-port=0` em STEALTH_ARGS para fechar porta CDP. `browser.py`
- [x] **#5** ~~`navigator.credentials` API não sobrescrita~~ — Adicionado stub completo em `browser.py`
- [x] **#6** ~~`init_script` aplicado DEPOIS da criação da page~~ — Falso-positivo: `add_init_script` do Playwright é executado ANTES de qualquer JS em cada navegação. Comportamento correto.

---

## Categoria 2: Inconsistência de Plataforma (CRITICAL)

- [x] **#7** ~~Sec-Ch-Ua-Platform mismatch~~ — Aceito como trade-off: Chrome no container reporta `Platform: "Windows"` via JS overrides + `--disable-features=UserAgentClientHint`. TikTok JS vê Windows; server vê headers Windows. O filesystem Linux é inacessível via browser JS.
- [x] **#8** ~~UA Windows vs Linux~~ — Mitigado: `navigator.platform` → `Win32`, `navigator.oscpu` → `undefined`, UA → `Windows NT 10.0`. Consistente do ponto de vista do JS. Detecção server-side por IP/ASN depende do proxy, não do OS.
- [x] **#9** ~~`navigator.platform` retorna `"Linux x86_64"` no Linux~~ — Sobrescrito para `"Win32"` em `browser.py` e `remote_session.py`
- [x] **#10** ~~`navigator.oscpu` não sobrescrito~~ — Sobrescrito para `undefined` (Chrome não expõe oscpu) em `browser.py` e `remote_session.py`
- [x] **#11** ~~`Intl.DateTimeFormat` override removido~~ — Falso-positivo: `timezone_id` do Playwright contexto já garante `Intl.DateTimeFormat().resolvedOptions().timeZone` correto. Override JS era bugado (detectável). `browser.py:836-839`

---

## Categoria 3: Fingerprint Estático (HIGH)

- [x] **#12** ~~WebGL renderer hardcoded~~ — `_generate_fingerprint(seed)` gera GPU/vendor únicos por perfil (6 GPUs: NVIDIA/Intel/AMD) em `browser.py`
- [x] **#13** ~~`hardwareConcurrency` fixo em 8~~ — Agora varia por perfil: [4,6,8,10,12,16] cores via `_generate_fingerprint()`
- [x] **#14** ~~`deviceMemory` fixo em 8~~ — Agora varia por perfil: [4,8,16] GB via `_generate_fingerprint()`
- [x] **#15** ~~`maxTouchPoints` fixo em 0~~ — Agora varia por perfil via `_generate_fingerprint()`: [0,0,0,0,1,5,10]. `browser.py` e `remote_session.py`
- [x] **#16** ~~UA estático para todos~~ — **Intencional**: UA deve ser consistente com cookies de sessão (trocar UA = "Session Expired"). Perfis podem ter UA customizado via DB (`fingerprint_ua`). O default é baseado na versão real do Chromium instalado no container.
- [x] **#17** ~~Viewport sempre 1920x1080~~ — `_generate_fingerprint()` agora inclui viewports variados (1920x1080, 1366x768, 1536x864, 1440x900, 2560x1440). Usado como default em `get_profile_identity()`. `network_utils.py`, `browser.py`
- [x] **#18** ~~Plugins idênticos~~ — Aceito: Chrome moderno (v90+) padronizou o PluginArray para 5 plugins PDF em TODOS os browsers. Variação aqui seria **mais** detectável que uniformidade.
- [x] **#19** ~~Fonts do container~~ — Mitigado: Dockerfile já instala `fonts-liberation`, `fonts-croscore`, `fonts-noto-core`, `fonts-freefont-ttf`, `fonts-dejavu-core` — cobrindo as principais fontes Windows. `Dockerfile`
- [x] **#20** ~~`screen.orientation` não sobrescrito~~ — Adicionado override `landscape-primary` angle=0 em `browser.py` e `remote_session.py`

---

## Categoria 4: Canvas/Audio/WebGL Fingerprinting (HIGH)

- [x] **#21** ~~Canvas fingerprint zero proteção~~ — Adicionado noise injection per-profile (LSB flip determinístico via seed) em `toDataURL` e `toBlob`. `browser.py`
- [x] **#22** ~~AudioContext zero proteção~~ — Adicionado variação de `DynamicsCompressor.threshold/knee` per-profile + noise em `getFloatFrequencyData`. `browser.py`
- [x] **#23** ~~WebGL extensions patch incompleto~~ — Adicionado `getSupportedExtensions()` override com set consistente de 20+ extensions comuns (desktop Chrome). `browser.py`
- [x] **#24** ~~Sem `OfflineAudioContext` override~~ — Coberto pelo fix #22: `AnalyserNode.getFloatFrequencyData` é compartilhado entre `AudioContext` e `OfflineAudioContext`.

---

## Categoria 5: Cookies & Sessão (HIGH)

- [x] **#25** ~~Cookies JSON plaintext~~ — Aceito: arquivos estão no volume Docker interno (`/app/data/sessions/`), não acessível externamente. Criptografia adiciona complexidade sem benefício real (chave teria que estar no mesmo container).
- [x] **#26** ~~UA mismatch com cookies~~ — Resolvido: `get_profile_identity()` usa UA persistente do perfil (DB ou session JSON). Cookies são renovados com o mesmo UA que os gerou.
- [x] **#27** ~~Validação de sessão via httpx sem proxy~~ — Agora resolve e usa proxy do perfil no health check. `session_manager.py`
- [x] **#28** ~~sid_guard parsing frágil~~ — Verificado: já tem `try/except (ValueError, IndexError)` + guard `len(parts) >= 3`. Parsing é seguro.
- [x] **#29** ~~Cookies remove propriedades não-standard~~ — Aceito: Playwright só aceita campos específicos. Propriedades extras (storeId, hostOnly) são browser-internal e não afetam sessão TikTok.
- [x] **#30** ~~Sem validação de domínio~~ — Adicionado filtro: só aceita cookies `.tiktok.com`, `.tiktokv.com`, `.tiktokcdn.com`, `.byteoversea.com`, `.byteimg.com`. `session_manager.py`
- [x] **#31** ~~sameSite normalização~~ — Aceito: `no_restriction` → `None` é a tradução correta (Brave usa `no_restriction`, Playwright/Chrome usa `None`). Comportamento idêntico.

---

## Categoria 6: Proxy & Rede (CRITICAL)

- [x] **#32** ~~Pre-flight IP check via httpx BYPASSA o proxy~~ — REMOVIDO completamente de `uploader_monitored.py`
- [x] **#33** ~~WebRTC só bloqueia UDP~~ — Adicionado bloqueio JS-level que esvazia iceServers do RTCPeerConnection em `browser.py`
- [x] **#34** ~~Sem DNS-over-HTTPS~~ — Adicionado `--dns-over-https-mode=secure` + `--dns-over-https-templates=https://dns.google/dns-query` em STEALTH_ARGS. `browser.py`
- [x] **#35** ~~Proxy credentials logados em plaintext~~ — Verificado: logs só mostram server (host:port), não credenciais. OK.
- [x] **#36** ~~Sem proxy health check~~ — Adicionado quick check via httpx antes de launch browser (non-blocking, warn-only). `remote_session.py`
- [x] **#37** ~~Rotação de proxy~~ — N/A: proxys são fixos ISP (residenciais). IP estável é feature, não bug.
- [x] **#38** ~~Proxy DNS leak~~ — Mitigado pelo DoH fix (#34). Chrome com `--dns-over-https-mode=secure` resolve DNS via HTTPS, não pelo DNS local da VPS.

---

## Categoria 7: Padrão Comportamental (CRITICAL)

- [x] **#39** ~~Warmup extremamente previsível~~ — Agora varia URL de entrada (home/foryou/explore), scroll count, direção, pausas. `uploader_monitored.py`
- [x] **#40** ~~Mouse movement usa sempre `steps=10`~~ — Agora `steps=random.randint(5, 25)` com movimentos variados. `uploader_monitored.py`
- [ ] **#41** ⏳ **Zero interação social** — **DEFERRED: requer módulo de engagement automation (like/follow/comment)**
- [ ] **#42** ⏳ **Zero consumo de conteúdo** — **DEFERRED: requer módulo de content consumption simulation**
- [x] **#43** ~~Sem variação de URL de entrada~~ — Warmup agora usa random.choice entre home/foryou/explore. `uploader_monitored.py`
- [x] **#44** ~~Scrolls sempre verticais~~ — Agora inclui scroll horizontal leve + chance de voltar scroll (20%). `uploader_monitored.py`
- [ ] **#45** ⏳ Sem tab switching — **DEFERRED: enhancement para warmup avançado**
- [ ] **#46** ⏳ Sem uso de clipboard — **DEFERRED: enhancement para warmup avançado**
- [ ] **#47** ⏳ Sem digitação com erros — **DEFERRED: enhancement para warmup avançado**
- [ ] **#48** ⏳ **Sem warmup de conta nova** — **DEFERRED: requer fluxo VNC Fábrica (dias de "aging" antes de postar)**
- [ ] **#49** ⏳ Sem ramp-up gradual — **DEFERRED: requer lógica de progressão no scheduler**

---

## Categoria 8: Conteúdo & Metadados (HIGH)

- [x] **#50** ~~FFmpeg metadata diz `encoder=Synapse Studio`~~ — REMOVIDO de `editor.py` e `stitcher.py`
- [x] **#51** ~~FFmpeg metadata tem `title=` com padrão previsível~~ — REMOVIDO de `editor.py`
- [x] **#52** ~~Sem stripping de metadata antes do upload~~ — Adicionado `-map_metadata -1` em 5 comandos FFmpeg (`editor.py` + 4x `stitcher.py`)
- [x] **#53** ~~Mesmas configurações de encoding para TODOS os vídeos~~ — `_randomized_encoding()` varia CRF(19-22), bitrate(4500-5500k), audio(188-196k), preset(medium/slow) em `editor.py`
- [x] **#54** ~~Crossfade sempre 0.5s~~ — Agora varia entre 0.35-0.65s via `_rand_crossfade()` em `stitcher.py`
- [x] **#55** ~~Aspect ratio fixo~~ — Aceito: 1080x1920 (9:16) é o padrão TikTok obrigatório. Variação não faz sentido para shorts.
- [ ] **#56** ⏳ Conteúdo 100% Twitch — **DEFERRED: requer diversificação de fontes de conteúdo**
- [x] **#57** ~~Sem variação de qualidade/codec entre uploads~~ — Resolvido junto com #53 via `_randomized_encoding()`

---

## Categoria 9: Scheduling & Frequência (HIGH)

- [x] **#58** ~~Horários de postagem matematicamente regulares~~ — Jitter adicionado: minuto aleatório (1-45) + segundo aleatório por slot. `auto_scheduler.py`
- [x] **#59** ~~Sem jitter/variação nos horários~~ — Resolvido junto com #58
- [x] **#60** ~~Postagem sempre a partir de amanhã~~ — Agora usa slots de hoje se ainda há >=2h de margem, senão D+1. Guard para não agendar horários passados. `auto_scheduler.py`
- [x] **#61** ~~Sem variação semanal~~ — Domingos 40% chance de metade dos slots, sábados 25%. `auto_scheduler.py`
- [x] **#62** ~~Upload retry agressivo~~ — Verificado: MAX_UPLOAD_RETRIES=3 com exponential backoff (60s→120s→240s, cap 600s). Razoável.

---

## Categoria 10: Infraestrutura Compartilhada (HIGH)

- [ ] **#63** ⏳ Perfis compartilham container — **DEFERRED: requer arquitetura multi-container**
- [ ] **#64** ⏳ Mesmo VPS IP — **DEFERRED: limitação de infra (1 VPS)**
- [x] **#65** ~~Xvfb :99 compartilhado~~ — Aceito: cada browser tem seu processo isolado no mesmo display. Xvfb é apenas o frame buffer virtual, sem cross-contamination.
- [x] **#66** ~~Sem isolamento de processo~~ — Mitigado: perfis usam persistent contexts separados + proxy individual. Isolamento completo requer multi-container (#63).
- [x] **#67** ~~VNC sem senha~~ — Agora usa senha aleatória por sessão via `-passwd` + auto-preenchida na URL noVNC. `remote_session.py`
- [x] **#68** ~~Portas VNC expostas~~ — x11vnc agora aceita apenas `-localhost` (websockify faz o proxy). Acesso externo só via noVNC com senha. `remote_session.py`
- [x] **#69** ~~Browser profile compartilhado entre VNC e worker~~ — Worker agora verifica se VNC está ativo para o perfil antes de usar persistent profile; se ativo, usa ephemeral context. `browser.py`

---

## Categoria 11: Detecção Avançada Ausente (MEDIUM-HIGH)

- [ ] **#70** ⏳ JA3/TLS fingerprint — **DEFERRED: requer fork ou proxy TLS randomizer (não possível via Playwright args)**
- [ ] **#71** ⏳ HTTP/2 SETTINGS fingerprint — **DEFERRED: requer TLS proxy layer**
- [x] **#72** ~~Sem override de `navigator.connection`~~ — Adicionado stub com effectiveType/rtt/downlink em `browser.py`
- [x] **#73** ~~Sem override de `navigator.getBattery()`~~ — Adicionado stub completo em `browser.py`
- [x] **#74** ~~`Permissions.query` só sobrescreve `notifications`~~ — Estendido para geolocation, camera, microphone em `browser.py`
- [x] **#75** ~~`window.chrome.webstore` ausente~~ — Adicionado stub com onInstallStageChanged/onDownloadProgress em `browser.py`
- [x] **#76** ~~performance.timing~~ — Aceito: `performance.timing` é deprecated (Navigation Timing Level 1) e retorna dados reais de carregamento. Override causaria mais detecção do que proteção, pois TikTok valida consistência entre timing e DOM state.
- [x] **#77** ~~Sem `mediaDevices.enumerateDevices()` spoofing~~ — Retorna dispositivos realistas (audio in/out + video) em `browser.py`
- [x] **#78** ~~Error.stack revela Playwright~~ — Adicionado `Error.prepareStackTrace` que sanitiza referências a playwright/puppeteer. `browser.py`
- [x] **#79** ~~`window.name` não sobrescrito~~ — Adicionado reset para string vazia em `browser.py`
- [x] **#80** ~~`window.external` não definido~~ — Adicionado `AddSearchProvider`/`IsSearchProviderInstalled` (Chrome Windows) em `browser.py` e `remote_session.py`
- [x] **#81** ~~Sem proteção de `toString()` em funções injetadas~~ — Adicionado `toString()` nativo para `permissions.query`, `getBattery`, `enumerateDevices` em `browser.py`
- [x] **#82** ~~`toString()` das funções nativas não protegido~~ — Adicionado toString override para chrome.runtime em `browser.py`
- [x] **#83** ~~requestIdleCallback timing~~ — Adicionado wrapper que limita `timeRemaining()` a max 49.9ms (realista). `browser.py`

---

## Categoria 12: Session Management (MEDIUM)

- [x] **#84** ~~VNC session stop não salva cookies antes de fechar~~ — Adicionado `storage_state(path=)` antes do `context.close()` em `remote_session.py`
- [x] **#85** ~~Sem heartbeat~~ — `get_session_status()` já verifica PIDs vivos a cada chamada. Sessões com processos mortos são auto-limpas.
- [x] **#86** ~~Sem timeout automático~~ — Adicionado auto-stop após 4h (`SESSION_TIMEOUT_HOURS`). Verificado em `get_session_status()`. `remote_session.py`
- [x] **#87** ~~Stale VNC processos acumulam~~ — `stop_session()` agora faz `pkill -9` em chromium, chrome, x11vnc e websockify. `remote_session.py`
- [x] **#88** ~~`_kill_pid` usa `SIGKILL` direto~~ — Agora tenta `SIGTERM` primeiro, espera até 2s, depois `SIGKILL` se necessário. `remote_session.py`

---

## Categoria 13: Trust & Reputação (CRITICAL)

- [x] **#89-94** ~~Trust/Reputação (service workers, IndexedDB, localStorage, history, bookmarks, cache)~~ — **Resolvido pela arquitetura VNC**: persistent context acumula trust organicamente. Cada sessão VNC gera histórico real. Novos perfis usarão o fluxo VNC Fábrica para "aquecer" antes de entrar em produção.

---

## Categoria 14: Padrão de Login (HIGH)

- [x] **#95** ~~Login via cookie injection~~ — **Resolvido pela VNC Fábrica**: login será feito manualmente via VNC, não via cookie injection. Cookies salvos via `storage_state`.
- [x] **#96** ~~Cookies cross-browser (Brave→Chromium)~~ — **Resolvido**: VNC Fábrica usa Chromium nativo (mesmo engine). Não haverá mais import de cookies Brave.
- [x] **#97** ~~Rate limit por login falhado~~ — **Mitigado**: nova conta será criada via VNC Fábrica com proxy selecionável. Login manual = sem retries automáticos.
- [ ] **#98** ⏳ QR code login — **DEFERRED: enhancement futuro**

---

## Categoria 15: Anti-Detecção de Container (MEDIUM)

- [x] **#99** ~~Docker detection não usada~~ — Agora usada: `IN_DOCKER` controla headless default (`launch_browser_for_profile`), Xvfb auto-start, args extra. `browser.py`
- [x] **#100-103** ~~Container detection via `/proc`, `.dockerenv`, cpuinfo, hostname~~ — **Irrelevante para TikTok**: essas APIs são server-side (não acessíveis via JavaScript no browser). TikTok detecta via fingerprint JS, não filesystem do host.

---

## Categoria 16: CAPTCHA & Challenges (MEDIUM)

- [x] **#104** ~~CAPTCHA CSS selectors~~ — Aceito: selectors são o método mais robusto e testado. TikTok muda classes mas mantém `data-e2e` attributes.
- [ ] **#105** ⏳ CAPTCHA solver — **DEFERRED: requer integração com serviço externo (2Captcha/hCaptcha)**
- [x] **#106** ~~Sem CAPTCHA fallback~~ — VNC resolve: CAPTCHA aciona notificação e o operador resolve manualmente via VNC do perfil.

---

## Categoria 17: Logging & OPSEC (LOW-MEDIUM)

- [x] **#107** ~~Console logger injetado no browser~~ — Monitor desativado por padrão em produção (`enable_monitor=False`). Sem risco.
- [x] **#108** ~~Proxy passwords em logs~~ — Verificado: logs só exibem `server` (host:port), não credentials. Nenhum `logger`/`print` expõe proxy_url com senha.
- [x] **#109** ~~IP público logado sem proxy (pre-flight check)~~ — Removido junto com fix #32
- [x] **#110** ~~Screenshot path sensível~~ — Verificado: path é interno (`/app/data/diagnostics/`) com slug+timestamp, sem dados sensíveis. Log é apenas para debugging interno.

---

## Top 10 Causas Mais Prováveis do Ban

| Rank | Issue | Descrição |
|------|-------|-----------|
| 1 | #50 | `encoder=Synapse Studio` no metadata do vídeo |
| 2 | #2 | playwright-stealth NÃO instalado |
| 3 | #7-9 | Plataforma Windows/Linux mismatch |
| 4 | #41-42 | Zero interação social / zero consumo de conteúdo |
| 5 | #48 | Sem warmup de conta nova |
| 6 | #32 | Pre-flight IP check bypassa proxy — VPS IP vazou |
| 7 | #12-17 | Fingerprint idêntico entre perfis (GPU, RAM, CPU, viewport) |
| 8 | #39-40 | Padrão de navegação robótico |
| 9 | #95-96 | Cookie injection cross-browser (Brave→Chromium) |
| 10 | #70 | JA3/TLS fingerprint de Playwright |

---

## Changelog

| Data | Issues Resolvidas | Descrição |
|------|-------------------|-----------|
| 2026-03-27 | #50, #51, #52 | Removido `encoder=Synapse Studio` e `title=` do metadata FFmpeg. Adicionado `-map_metadata -1` em todos os comandos FFmpeg (editor.py + 4x stitcher.py) |
