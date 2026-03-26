# Analise de Viabilidade — Plano Anti-Shadowban
**Data:** 2026-03-26
**Pipeline:** Synapse Clipper (FFmpeg + Whisper + ASS)

---

## 🟢 Tier 1 — Alterações Rápidas (TODAS VIÁVEIS)

### 1. Micro-variação de Pitch/Velocidade
- **Veredicto:** VIÁVEL
- **Como:** FFmpeg `setpts=PTS/1.02` (video) + `atempo=1.02` (audio). Sorteio entre 1.01x–1.04x no `editor.py` antes do encode.
- **Esforço:** ~5 linhas de código
- **Onde:** `backend/core/clipper/editor.py` → cmd do FFmpeg

### 2. Grain Overlay (1-3%)
- **Veredicto:** VIÁVEL
- **Como:** FFmpeg filtro `noise=c0s=3:c1s=3:c2s=3:allf=t+u` adicionado ao filter_complex.
- **Esforço:** ~3 linhas de código
- **Onde:** `backend/core/clipper/editor.py` → filter_complex de cada layout

### 3. Color Grading Aleatório
- **Veredicto:** VIÁVEL
- **Como:** FFmpeg `eq=contrast=1.03:saturation=0.98:brightness=0.01` com valores sorteados de uma lista pré-definida de 5 presets.
- **Esforço:** ~10 linhas de código
- **Onde:** `backend/core/clipper/editor.py` → filter_complex (antes do encode final)

### 4. Metadados Ricos (Slug + EXIF)
- **Veredicto:** VIÁVEL
- **Como:** Já temos Oracle gerando captions. Adicionar `-metadata title="..."` no cmd FFmpeg e renomear output com slug dinâmico (ex: `alanzoka_susto_fnaf_26032026_a3f2.mp4`).
- **Esforço:** ~8 linhas de código
- **Onde:** `backend/core/clipper/editor.py` (metadata) + `backend/core/clipper/worker.py` (slug)

**Esforço total Tier 1: ~1-2 horas de implementação.**

---

## 🟡 Tier 2 — Dinâmica Visual de Retenção

### 5. Ken Burns Effect (Zoom Dinâmico)
- **Veredicto:** VIÁVEL
- **Como:** FFmpeg `zoompan=z='min(zoom+0.0003,1.06)':d=N:s=1080x1920`. Aplicável nos layouts podcast/street onde a câmera é estática. Precisa calibrar o ritmo do zoom para não parecer "drift" genérico.
- **Esforço:** Média complexidade (~15 linhas)
- **Onde:** `backend/core/clipper/editor.py` → `_build_edit_filter_podcast()` e `_build_edit_filter_street()`

### 6. Layouts Geométricos Rotativos
- **Veredicto:** PARCIALMENTE VIÁVEL
- **Detalhes:**
  - Variação de proporção (30/70, 40/60, 50/50) = trivial. Já temos `FACECAM_RATIO` como constante, basta sortear por job.
  - Bordas arredondadas via FFmpeg `geq` = possível mas +30% tempo de encode.
  - Câmera flutuante PiP = viável mas exige novo filter_graph completo.
- **Esforço:** Baixo (proporção) a Alto (PiP flutuante)
- **Onde:** `backend/core/clipper/editor.py` → `_build_edit_filter_facecam()`

### 7. Trilha Sonora BGM com Seek Aleatório
- **Veredicto:** VIÁVEL, COM IMPEDIMENTO
- **Como:** FFmpeg `amix` para mixar audio em volume baixo (-20dB) é trivial. Seek aleatório = `-ss {random}` no input.
- **Impedimento:** Precisamos de um banco de músicas royalty-free dentro do container. Solução: bundle 5-10 tracks lofi/phonk (~50MB total) no build Docker, ou bucket MinIO dedicado.
- **Esforço:** ~1h de código + sourcing de assets musicais

---

## 🔴 Tier 3 — Evoluções Orgânicas e Legendagem

### 8. Fonte e Estilo de Legenda Variável por Perfil
- **Veredicto:** VIÁVEL
- **Detalhes:**
  - Já existem 4 estilos no `subtitle_engine.py`: opus, neon, cyan, minimal.
  - Adicionar 2-3 fontes extras (Montserrat, Roboto Black) requer instalá-las no Dockerfile.
  - Sortear estilo por job = ~5 linhas no worker.
  - Cor de branding do streamer: precisa mapear manualmente ou extrair do `profile_image_url` com PIL (média complexidade).
- **Esforço:** Baixo (sorteio) a Médio (branding colors)
- **Onde:** `backend/core/clipper/worker.py` (sorteio) + `subtitle_engine.py` (novos estilos) + `Dockerfile` (fontes)

### 9. Jump Cut por Silêncio (Zoom na Cara)
- **Veredicto:** VIÁVEL
- **Detalhes:**
  - Já temos timestamps word-level do Whisper. Detectar gaps > 400ms e inserir zoom (scale 1.0→1.15 em 200ms) é factível via filter_complex dinâmico.
  - Complexidade alta no FFmpeg filter graph (múltiplos `trim` + `zoompan` + `concat`), mas possível.
- **Esforço:** Alto (~50 linhas de filter graph dinâmico)
- **Onde:** `backend/core/clipper/editor.py` (novo filtro) + `worker.py` (passar timestamps)

### 10. B-Roll Contextual (AI-Driven Inserts)
- **Veredicto:** INVIÁVEL NO CURTO PRAZO
- **Impedimentos:**
  1. Não temos banco de imagens/vídeos indexado por keyword.
  2. APIs externas (Pexels, Unsplash) têm rate limits e latência incompatíveis com pipeline batch.
  3. LLM analisando transcrição + matching semântico + PiP dinâmico com timing frame-accurate = cada item é um subprojeto.
- **Alternativa futura:** Criar bucket MinIO com assets categorizados manualmente. LLM faz matching por tag. Mas exige curadoria humana dos assets.

### 11. Face-Tracking Dinâmico + Camera Shake (MrBeastification)
- **Veredicto:** PARCIALMENTE VIÁVEL
- **Detalhes:**
  - Já temos `detect_facecam_box()` via MTCNN, mas é single-frame (1 análise por clip).
  - Tracking frame-a-frame com mediapipe/OpenCV é viável mas aumentaria tempo de processamento em 5-10x.
  - **VAD via Whisper é grátis** — já temos os word timestamps, detectar picos de energia é possível.
  - Camera shake via FFmpeg `lenscorrection` ou `rotate` com valores randomizados é factível.
- **Impedimento principal:** Tempo de processamento na VPS (sem GPU dedicada).
- **Esforço:** Muito alto

### 12. Elementos Nativos Fake (Comentários, Emojis)
- **Veredicto:** PARCIALMENTE VIÁVEL
- **Detalhes:**
  - Balões de comentário = overlay de PNG animado posicionado via FFmpeg `overlay` com timing.
  - Emojis seguindo palavras-gatilho = mesma lógica, usando timestamps do Whisper.
- **Impedimento:** Criação dos assets visuais (design work, não código). Precisa de templates PNG/APNG dos balões e emojis.
- **Esforço:** Médio (código) + Design (assets)

### 13. Sound Effects (SFX) nos Textos
- **Veredicto:** VIÁVEL
- **Detalhes:**
  - Similar ao BGM — precisa de pack de SFX (whoosh, pop, ding — ~5MB).
  - FFmpeg `amix` com delay específico no timestamp da palavra exclamativa.
  - Whisper já fornece os timestamps. Detectar "!" ou palavras rápidas = regex no transcript.
- **Esforço:** ~30 linhas de código + pack de assets de áudio
- **Onde:** `backend/core/clipper/editor.py` ou novo módulo `sfx_engine.py`

### 14. Hook Inteligente Textual (Título nos 3 primeiros seg.)
- **Veredicto:** VIÁVEL
- **Detalhes:**
  - Oracle já gera caption/título.
  - Criar evento ASS nos primeiros 3 segundos: fonte grande + fade-in + fade-out.
  - Direto no `subtitle_engine.py` como primeiro evento do arquivo .ass.
- **Esforço:** ~20 linhas de código
- **Onde:** `backend/core/clipper/subtitle_engine.py` + `worker.py` (passar título)

### 15. Legendas Sinfônicas (Audio-Reactive Text)
- **Veredicto:** INVIÁVEL COM FFMPEG
- **Impedimentos:**
  1. Exige análise RMS frame-a-frame do áudio (librosa/numpy).
  2. Renderização de texto com tamanho dinâmico proporcional ao volume — FFmpeg não suporta nativamente.
  3. Alternativa `drawtext` com expressões FFmpeg é extremamente limitada e frágil.
  4. Pipeline Python custom (librosa + PIL renderizando frame-by-frame) adicionaria minutos ao processamento de cada clip.
- **Alternativa:** Usar Whisper confidence scores para variar levemente o tamanho da fonte por palavra (proxy grosseiro, mas factível via ASS). Não é "sinfônico" de verdade, mas adiciona variabilidade.

### 16. Falso Parallax 3D (Depth-Mapping)
- **Veredicto:** INVIÁVEL
- **Impedimentos:**
  1. Segmentação de profundidade requer modelos AI (mediapipe selfie segmentation ou MiDaS).
  2. Processamento GPU frame-a-frame. Na VPS atual (sem GPU dedicada), levaria 10-30 min por clipe de 60s.
  3. Totalmente inviável no pipeline batch com o hardware atual.
- **Viabilidade futura:** Apenas com GPU dedicada (RTX 3060+) e mediapipe otimizado.

---

## Resumo de Viabilidade

| Categoria | Itens viáveis | Com impedimento | Inviáveis |
|-----------|:---:|:---:|:---:|
| 🟢 Tier 1 | **4/4** | 0 | 0 |
| 🟡 Tier 2 | **2/3** | 1 (BGM: assets) | 0 |
| 🔴 Tier 3 | **4/9** | 3 | **2** |
| **Total** | **10/16** | **4/16** | **2/16** |

---

## Roadmap de Implementação Recomendado

### Fase 1 — Bypass de Hash (Imediato, ~1-2h)
1. Grain overlay (1-3%)
2. Speed jitter (1.01x–1.04x)
3. Color grading aleatório (5 presets)
4. Metadados ricos (título + slug)

### Fase 2 — Retenção Visual (~3-4h)
5. Hook textual nos 3 primeiros segundos
6. Variação de estilo de legenda por job (sortear entre opus/neon/cyan)
7. Ken Burns nos layouts podcast/street

### Fase 3 — Edição Premium (~1 dia)
8. SFX em palavras de impacto (precisa pack de áudio)
9. BGM lofi/phonk em volume baixo (precisa tracks)
10. Variação de proporção facecam (30/70, 40/60, 50/50)

### Fase 4 — Edição Avançada (Futuro)
11. Jump cuts por silêncio com zoom
12. Overlays de comentários fake
13. Face-tracking dinâmico (requer GPU)

---

*Análise realizada sobre a codebase do Synapse Clipper em 2026-03-26.*
*Pipeline: FFmpeg + faster-whisper + ASS (libass) + MTCNN + Oracle LLM (Groq).*
