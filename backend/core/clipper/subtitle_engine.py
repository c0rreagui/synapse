"""
Clipper Subtitle Engine - Gerador de Legendas ASS Animadas
============================================================

Converte output word-level do faster-whisper em arquivo .ass (Advanced
SubStation Alpha) com animacoes "pop-in" estilo Opus Clip.

Efeitos implementados:
    - Pop-in: Palavra escala de 0% -> 100% em ~150ms ao aparecer
    - Cor ativa: Palavra sendo falada em cor destaque (amarelo/verde neon)
    - Outline forte: Borda preta para legibilidade sobre qualquer fundo
    - Posicao: Centro inferior do frame 9:16

Formato ASS:
    O .ass e renderizado diretamente pelo FFmpeg via filtro "ass" (libass).
    Nao requer dependencias extras alem do FFmpeg compilado com libass.
"""

import os
import uuid
import logging
import textwrap
import re
from typing import List, Dict, Any, Optional

from core.config import DATA_DIR

logger = logging.getLogger("SubtitleEngine")

# Diretorio para legendas geradas
SUBS_DIR = os.path.join(DATA_DIR, "clipper", "subs")
os.makedirs(SUBS_DIR, exist_ok=True)


# ─── Configuracao de Estilos ────────────────────────────────────────────

# Cores do Neo-Glass Design System (formato ASS: &HAABBGGRR)
COLOR_WHITE = "&H00FFFFFF"
COLOR_CYAN = "&H00D4B606"               # #06b6d4
COLOR_GREEN = "&H0081B910"              # #10b981
COLOR_YELLOW = "&H000B9EF5"             # #f59e0b
COLOR_PURPLE = "&H00F65C8B"             # #8b5cf6
COLOR_OUTLINE_BLACK = "&H00000000"
COLOR_SHADOW = "&H80000000"             # Preto semi-transparente

# Fonte padrao - Inter Black (instalada no container via Dockerfile)
DEFAULT_FONT = "Inter Black"
DEFAULT_FONT_SIZE = 85
OUTLINE_SIZE = 7
SHADOW_DEPTH = 4

# Timing do pop-in (ms)
POPIN_DURATION_MS = 80
POPIN_SCALE_START = 115  # Comeca em 115% do tamanho (micro-zoom)

# Hold padding: texto permanece visivel apos o audio terminar (ms)
HOLD_PADDING_MS = 800

# Margem inferior (distancia do bottom em pixels, para frame 1080x1920)
# Ajustado para 0 pois o Alignment=5 vai centralizar as legendas no equador da tela (Y=960)
MARGIN_BOTTOM = 0

# Maximo de palavras por bloco visual (estilo Hormozi: 2-3 palavras max)
MAX_WORDS_PER_BLOCK = 3

# Corte forcado por silencio: se o gap entre palavras > este valor,
# quebra o bloco imediatamente independente do limite de palavras
SILENCE_BREAK_MS = 400


class SubtitleStyle:
    """Configuracao de estilo para as legendas."""

    def __init__(
        self,
        name: str = "opus",
        font: str = DEFAULT_FONT,
        font_size: int = DEFAULT_FONT_SIZE,
        active_color: str = COLOR_YELLOW,
        inactive_color: str = COLOR_WHITE,
        outline_color: str = COLOR_OUTLINE_BLACK,
        outline_size: int = OUTLINE_SIZE,
        shadow_depth: int = SHADOW_DEPTH,
        shadow_color: str = COLOR_SHADOW,
        margin_bottom: int = MARGIN_BOTTOM,
        popin_ms: int = POPIN_DURATION_MS,
        popin_scale_start: int = POPIN_SCALE_START,
    ):
        self.name = name
        self.font = font
        self.font_size = font_size
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.outline_color = outline_color
        self.outline_size = outline_size
        self.shadow_depth = shadow_depth
        self.shadow_color = shadow_color
        self.margin_bottom = margin_bottom
        self.popin_ms = popin_ms
        self.popin_scale_start = popin_scale_start


# Estilos pre-definidos
STYLES = {
    "opus": SubtitleStyle(
        name="opus",
        active_color=COLOR_YELLOW,
        font_size=85,
    ),
    "neon": SubtitleStyle(
        name="neon",
        active_color=COLOR_GREEN,
        font_size=90,
        outline_size=8,
    ),
    "cyan": SubtitleStyle(
        name="cyan",
        active_color=COLOR_CYAN,
        font_size=85,
        outline_size=7,
    ),
    "minimal": SubtitleStyle(
        name="minimal",
        active_color=COLOR_WHITE,
        font_size=80,
        outline_size=5,
        shadow_depth=0,
        popin_ms=0,
    ),
}


# ─── Funcoes de Formatacao ASS ──────────────────────────────────────────

def _ass_timestamp(seconds: float) -> str:
    """Converte segundos para formato de timestamp ASS: h:mm:ss.cc"""
    # Clamp para evitar timestamps negativos que quebram o formato ASS
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _build_ass_header(style: SubtitleStyle, video_width: int = 1080, video_height: int = 1920) -> str:
    """Gera o cabecalho do arquivo .ass com definicoes de estilo."""
    return f"""[Script Info]
Title: Synapse Auto Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Active,{style.font},{style.font_size},{style.active_color},{style.active_color},{style.outline_color},{style.shadow_color},-1,0,0,0,100,100,1,0,1,{style.outline_size},{style.shadow_depth},5,40,40,{style.margin_bottom},1
Style: Inactive,{style.font},{style.font_size},{style.inactive_color},{style.inactive_color},{style.outline_color},{style.shadow_color},-1,0,0,0,100,100,1,0,1,{style.outline_size},{style.shadow_depth},5,40,40,{style.margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _build_word_popin_tag(style: SubtitleStyle) -> str:
    """Tag ASS para efeito pop-in: escala de X% -> 100% em N ms."""
    if style.popin_ms <= 0:
        return ""
    s = style.popin_scale_start
    ms = style.popin_ms
    return f"{{\\fscx{s}\\fscy{s}\\t(0,{ms},\\fscx100\\fscy100)}}"


def _build_word_active_tag(style: SubtitleStyle) -> str:
    """Tag ASS para cor da palavra ativa."""
    return f"{{\\1c{style.active_color}}}"


def _build_word_inactive_tag(style: SubtitleStyle) -> str:
    """Tag ASS para cor da palavra inativa (ja falada ou proxima)."""
    return f"{{\\1c{style.inactive_color}}}"


# ─── Gerador Principal ──────────────────────────────────────────────────

def _group_words_into_blocks(words: List[Dict], max_per_block: int = MAX_WORDS_PER_BLOCK) -> List[List[Dict]]:
    """
    Agrupa palavras em blocos visuais com duas regras de corte:
    1. Limite maximo de palavras por bloco (MAX_WORDS_PER_BLOCK)
    2. Silencio entre palavras > SILENCE_BREAK_MS forca um corte
       imediato, mesmo que o bloco nao tenha atingido o limite.
    """
    silence_threshold = SILENCE_BREAK_MS / 1000.0  # converter para segundos
    blocks = []
    current_block = []

    for word in words:
        # Verificar gap de silencio com a palavra anterior
        if current_block:
            prev_end = current_block[-1]["end"]
            curr_start = word["start"]
            gap = curr_start - prev_end

            if gap >= silence_threshold:
                # Silencio detectado: fechar bloco atual
                blocks.append(current_block)
                current_block = []

        current_block.append(word)

        if len(current_block) >= max_per_block:
            blocks.append(current_block)
            current_block = []

    if current_block:
        blocks.append(current_block)

    return blocks


def generate_ass(
    whisper_result: Dict[str, Any],
    style_name: str = "opus",
    output_path: Optional[str] = None,
    video_width: int = 1080,
    video_height: int = 1920,
) -> str:
    """
    Gera arquivo .ass com legendas animadas a partir do resultado do Whisper.

    Para cada bloco de palavras:
      - O bloco inteiro e exibido durante o intervalo [start_primeira..end_ultima]
      - Cada palavra recebe pop-in individual quando chega seu timestamp
      - Palavra ativa = cor destaque, demais = branco

    Args:
        whisper_result: Output do transcriber (deve conter "words")
        style_name: Nome do estilo pre-definido ("opus", "neon", "minimal")
        output_path: Caminho de saida. Se None, gera em SUBS_DIR.
        video_width: Largura do video target
        video_height: Altura do video target

    Returns:
        Caminho absoluto do arquivo .ass gerado
    """
    style = STYLES.get(style_name, STYLES["opus"])
    words = whisper_result.get("words", [])

    # Filtro de Ruido Tipografico: remover , . ; : mantendo ? e !
    # Compiled here to avoid recompiling it O(N) times inside the loop
    clean_pattern = re.compile(r'[,.;:]')
    for w in words:
        if "word" in w:
            w["word"] = clean_pattern.sub('', w["word"])

    if not words:
        logger.warning("Nenhuma palavra para gerar legendas. Gerando .ass vazio.")

    if output_path is None:
        # uuid4 garante unicidade sem collision (id() é não-determinístico)
        output_path = os.path.join(SUBS_DIR, f"subtitles_{uuid.uuid4().hex}.ass")
    
    assert output_path is not None

    # Construir .ass
    ass_content = _build_ass_header(style, video_width, video_height)
    blocks = _group_words_into_blocks(words)
    dialogue_lines = _generate_dialogue_lines(blocks, style)
    ass_content += "\n".join(dialogue_lines)

    # Salvar
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    logger.info(
        f"Legenda ASS gerada: {output_path} "
        f"({len(words)} palavras, {len(blocks)} blocos, estilo={style_name})"
    )
    return output_path


def _generate_dialogue_lines(blocks: List[List[Dict]], style: SubtitleStyle) -> List[str]:
    """
    Gera as linhas Dialogue do .ass para todos os blocos.
    Otimizado para nao rodar multiplicacoes quadraticas de array string.
    """
    lines = []
    popin_tag = _build_word_popin_tag(style)
    active_tag = _build_word_active_tag(style)
    inactive_tag = _build_word_inactive_tag(style)

    for block in blocks:
        if not block:
            continue

        block_start = block[0]["start"]
        block_end = block[-1]["end"]

        # Hold padding: texto permanece visivel por +400ms apos o audio
        block_end = block_end + (HOLD_PADDING_MS / 1000.0)

        # Pre-process static string list to avoid O(N^2) allocations per word slice
        words_inactive = [f"{inactive_tag}{w['word']}" for w in block]
        words_active = [f"{active_tag}{popin_tag}{w['word']}" for w in block]

        for word_idx, active_word in enumerate(block):
            word_start = active_word["start"]
            word_end = active_word["end"]

            ws = _ass_timestamp(word_start)
            we = _ass_timestamp(word_end)

            # Build line instantly taking the active from words_active and others from inactive
            text_parts = words_inactive[:]
            text_parts[word_idx] = words_active[word_idx]
            
            full_text = " ".join(text_parts)
            lines.append(f"Dialogue: 0,{ws},{we},Active,,0,0,0,,{full_text}")

    return lines


def generate_ass_for_multiple(
    transcriptions: List[Dict[str, Any]],
    style_name: str = "opus",
    output_path: Optional[str] = None,
    time_offsets: Optional[List[float]] = None,
) -> str:
    """
    Gera um unico .ass para multiplos clipes (pos-stitching).

    Cada transcricao recebe um offset de tempo para alinhar com a
    posicao do clipe no video final costurado.

    Args:
        transcriptions: Lista de resultados do Whisper
        style_name: Estilo visual
        output_path: Caminho de saida
        time_offsets: Lista de offsets em segundos para cada transcricao.
                      Se None, assume [0, duracao_clip1, duracao_clip1+clip2, ...]

    Returns:
        Caminho do .ass gerado
    """
    # Calcular offsets automaticos se nao fornecidos
    if time_offsets is None:
        time_offsets = []
        cumulative = 0.0
        for t in transcriptions:
            time_offsets.append(cumulative)
            cumulative += t.get("duration", 0)

    # Merge todas as palavras com offsets aplicados
    merged_words = []
    for i, transcription in enumerate(transcriptions):
        offset = time_offsets[i] if i < len(time_offsets) else 0.0
        for word in transcription.get("words", []):
            merged_words.append({
                "word": word["word"],
                "start": word["start"] + offset,
                "end": word["end"] + offset,
            })

    merged_result = {
        "words": merged_words,
        "word_count": len(merged_words),
    }

    return generate_ass(merged_result, style_name=style_name, output_path=output_path)
