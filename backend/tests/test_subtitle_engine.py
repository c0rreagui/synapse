"""
Testes unitarios para o Subtitle Engine (core/clipper/subtitle_engine.py)
=========================================================================

Valida:
    - Geracao correta de tags ASS pop-in
    - Agrupamento de palavras em blocos
    - Timestamps ASS formatados corretamente
    - Cores ativa/inativa nas dialogue lines
    - Geracao de arquivo .ass completo a partir de mock Whisper output
"""

import os
import sys
import tempfile

import pytest

# Ajustar path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.clipper.subtitle_engine import (
    _ass_timestamp,
    _build_word_popin_tag,
    _build_word_active_tag,
    _build_word_inactive_tag,
    _group_words_into_blocks,
    _generate_dialogue_lines,
    generate_ass,
    generate_ass_for_multiple,
    SubtitleStyle,
    STYLES,
)


# ─── Fixtures ───────────────────────────────────────────────────────────

MOCK_WHISPER_RESULT = {
    "text": "isso aqui e muito top demais cara incrivel jogo",
    "language": "pt",
    "language_probability": 0.98,
    "duration": 5.5,
    "segments": [],
    "words": [
        {"word": "isso",      "start": 0.0,   "end": 0.3},
        {"word": "aqui",      "start": 0.35,  "end": 0.6},
        {"word": "e",         "start": 0.65,  "end": 0.75},
        {"word": "muito",     "start": 0.8,   "end": 1.1},
        {"word": "top",       "start": 1.15,  "end": 1.4},
        {"word": "demais",    "start": 1.45,  "end": 1.8},
        {"word": "cara",      "start": 1.85,  "end": 2.1},
        {"word": "incrivel",  "start": 2.5,   "end": 2.9},
        {"word": "jogo",      "start": 3.0,   "end": 3.3},
    ],
    "word_count": 9,
}


# ─── Testes de Formatacao ───────────────────────────────────────────────

class TestAssTimestamp:
    def test_zero(self):
        assert _ass_timestamp(0.0) == "0:00:00.00"

    def test_simple_seconds(self):
        assert _ass_timestamp(5.5) == "0:00:05.50"

    def test_minutes(self):
        assert _ass_timestamp(65.25) == "0:01:05.25"

    def test_hours(self):
        assert _ass_timestamp(3661.50) == "1:01:01.50"

    def test_fractional(self):
        result = _ass_timestamp(1.234)
        # 1.234s -> 23 centisegundos
        assert result == "0:00:01.23"


class TestPopinTag:
    def test_default_style(self):
        style = STYLES["opus"]
        tag = _build_word_popin_tag(style)
        assert "\\fscx" in tag
        assert "\\fscy" in tag
        assert "\\t" in tag
        assert "\\fscx100" in tag
        assert "\\fscy100" in tag

    def test_minimal_no_popin(self):
        style = STYLES["minimal"]
        tag = _build_word_popin_tag(style)
        assert tag == ""

    def test_custom_scale(self):
        style = SubtitleStyle(popin_scale_start=80, popin_ms=200)
        tag = _build_word_popin_tag(style)
        assert "\\fscx80" in tag
        assert "200" in tag


class TestColorTags:
    def test_active_color(self):
        style = STYLES["opus"]
        tag = _build_word_active_tag(style)
        assert "\\1c" in tag
        assert "&H0000FFFF" in tag  # amarelo

    def test_inactive_color(self):
        style = STYLES["opus"]
        tag = _build_word_inactive_tag(style)
        assert "\\1c" in tag
        assert "&H00FFFFFF" in tag  # branco

    def test_neon_active(self):
        style = STYLES["neon"]
        tag = _build_word_active_tag(style)
        assert "&H0000FF00" in tag  # verde


# ─── Testes de Agrupamento ──────────────────────────────────────────────

class TestWordGrouping:
    def test_groups_correct_size(self):
        words = MOCK_WHISPER_RESULT["words"]
        blocks = _group_words_into_blocks(words, max_per_block=6)
        assert len(blocks) == 2  # 9 palavras / 6 = 2 blocos
        assert len(blocks[0]) == 6
        assert len(blocks[1]) == 3

    def test_single_block(self):
        words = MOCK_WHISPER_RESULT["words"][:3]
        blocks = _group_words_into_blocks(words, max_per_block=10)
        assert len(blocks) == 1
        assert len(blocks[0]) == 3

    def test_exact_fit(self):
        words = MOCK_WHISPER_RESULT["words"][:6]
        blocks = _group_words_into_blocks(words, max_per_block=6)
        assert len(blocks) == 1
        assert len(blocks[0]) == 6

    def test_empty_words(self):
        blocks = _group_words_into_blocks([], max_per_block=6)
        assert blocks == []


# ─── Testes de Dialogue Lines ───────────────────────────────────────────

class TestDialogueLines:
    def test_generates_lines(self):
        words = MOCK_WHISPER_RESULT["words"][:3]
        blocks = _group_words_into_blocks(words, max_per_block=6)
        style = STYLES["opus"]
        lines = _generate_dialogue_lines(blocks, style)
        # 3 palavras = 3 linhas de dialogo (uma para cada palavra ativa)
        assert len(lines) == 3

    def test_dialogue_format(self):
        words = MOCK_WHISPER_RESULT["words"][:2]
        blocks = _group_words_into_blocks(words, max_per_block=6)
        style = STYLES["opus"]
        lines = _generate_dialogue_lines(blocks, style)
        for line in lines:
            assert line.startswith("Dialogue: 0,")
            assert ",Active," in line

    def test_active_word_highlighted(self):
        words = [
            {"word": "alfa", "start": 0.0, "end": 0.5},
            {"word": "beta", "start": 0.6, "end": 1.0},
        ]
        blocks = _group_words_into_blocks(words, max_per_block=6)
        style = STYLES["opus"]
        lines = _generate_dialogue_lines(blocks, style)
        # Primeira linha: "alfa" e ativa, "beta" e inativa
        assert "&H0000FFFF" in lines[0]  # cor ativa (amarelo) presente
        assert "&H00FFFFFF" in lines[0]  # cor inativa (branco) presente


# ─── Testes de Geracao Completa ─────────────────────────────────────────

class TestGenerateAss:
    def test_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f:
            path = f.name

        try:
            result = generate_ass(MOCK_WHISPER_RESULT, output_path=path)
            assert result == path
            assert os.path.exists(path)
            assert os.path.getsize(path) > 100

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "[Script Info]" in content
                assert "[V4+ Styles]" in content
                assert "[Events]" in content
                assert "Dialogue:" in content
        finally:
            os.unlink(path)

    def test_empty_words(self):
        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f:
            path = f.name

        try:
            result = generate_ass({"words": []}, output_path=path)
            assert os.path.exists(result)
            content = open(result, "r", encoding="utf-8").read()
            assert "[Script Info]" in content
            # Sem Dialogue lines
            assert "Dialogue:" not in content
        finally:
            os.unlink(path)

    def test_style_selection(self):
        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f:
            path = f.name

        try:
            generate_ass(MOCK_WHISPER_RESULT, style_name="neon", output_path=path)
            content = open(path, "r", encoding="utf-8").read()
            assert "&H0000FF00" in content  # verde neon na linha de estilo
        finally:
            os.unlink(path)


class TestGenerateAssForMultiple:
    def test_merges_transcriptions(self):
        t1 = {"words": [{"word": "oi", "start": 0.0, "end": 0.5}], "duration": 1.0}
        t2 = {"words": [{"word": "tchau", "start": 0.0, "end": 0.5}], "duration": 1.0}

        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f:
            path = f.name

        try:
            result = generate_ass_for_multiple([t1, t2], output_path=path)
            assert os.path.exists(result)
            content = open(result, "r", encoding="utf-8").read()
            assert "oi" in content
            assert "tchau" in content
        finally:
            os.unlink(path)

    def test_applies_time_offsets(self):
        t1 = {"words": [{"word": "a", "start": 0.0, "end": 0.5}], "duration": 30.0}
        t2 = {"words": [{"word": "b", "start": 0.0, "end": 0.5}], "duration": 30.0}

        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f:
            path = f.name

        try:
            generate_ass_for_multiple([t1, t2], output_path=path, time_offsets=[0.0, 30.0])
            content = open(path, "r", encoding="utf-8").read()
            # "b" deve ter offset de 30s, entao timestamp ~0:00:30.00
            assert "0:00:30" in content
        finally:
            os.unlink(path)
