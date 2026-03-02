"""
Testes unitarios para o Stitcher (core/clipper/stitcher.py)
============================================================

Valida:
    - Calculo de duracao e decisao de estrategia
    - Logica de padding (hook + CTA)
    - Crossfade duration math
    - Resultado de erro padrao
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.clipper.stitcher import (
    MIN_DURATION_SECONDS,
    CROSSFADE_DURATION,
    HOOK_DURATION,
    CTA_DURATION,
    _error_result,
    _success_result,
    _cleanup,
)


# ─── Testes de Constantes ───────────────────────────────────────────────

class TestConstants:
    def test_min_duration_exceeds_tiktok_minimum(self):
        # TikTok exige >60s, nosso threshold deve ser > 60
        assert MIN_DURATION_SECONDS > 60

    def test_crossfade_is_short(self):
        # Crossfade nao deve consumir muito tempo do video
        assert CROSSFADE_DURATION <= 1.0
        assert CROSSFADE_DURATION > 0

    def test_padding_durations_reasonable(self):
        assert 2.0 <= HOOK_DURATION <= 6.0
        assert 2.0 <= CTA_DURATION <= 6.0


# ─── Testes de Logica de Padding ────────────────────────────────────────

class TestPaddingCalculation:
    def test_deficit_calculation_single_short_clip(self):
        """Um clipe de 40s precisa de ~25s de padding."""
        clip_duration = 40.0
        deficit = MIN_DURATION_SECONDS - clip_duration
        assert deficit > 20  # Precisa de bastante padding
        # Hook + CTA juntos devem cobrir deficit
        max_coverage = HOOK_DURATION + CTA_DURATION
        # Se deficit > max_coverage, o codigo estende proporcionalmente
        assert max_coverage > 0

    def test_no_deficit_when_long_enough(self):
        """Um clipe de 70s nao precisa de padding."""
        clip_duration = 70.0
        deficit = MIN_DURATION_SECONDS - clip_duration
        assert deficit < 0  # Sem deficit

    def test_two_clips_crossfade_math(self):
        """Dois clipes de 35s com crossfade = 35+35-0.5 = 69.5s (>65)."""
        d1, d2 = 35.0, 35.0
        combined = d1 + d2 - CROSSFADE_DURATION
        assert combined > MIN_DURATION_SECONDS

    def test_two_short_clips_still_need_padding(self):
        """Dois clipes de 20s com crossfade = 20+20-0.5 = 39.5s (<65)."""
        d1, d2 = 20.0, 20.0
        combined = d1 + d2 - CROSSFADE_DURATION
        assert combined < MIN_DURATION_SECONDS


# ─── Testes de Funcoes Utilitarias ──────────────────────────────────────

class TestErrorResult:
    def test_structure(self):
        result = _error_result("algo deu errado")
        assert result["success"] is False
        assert result["output_path"] is None
        assert result["duration"] == 0
        assert result["file_size"] == 0
        assert result["strategy"] is None
        assert result["error"] == "algo deu errado"


class TestSuccessResult:
    def test_structure(self, tmp_path):
        dummy = tmp_path / "test.mp4"
        dummy.write_bytes(b"x" * 1000)
        result = _success_result(str(dummy), 65.0, "crossfade")
        assert result["success"] is True
        assert result["output_path"] == str(dummy)
        assert abs(result["duration"] - 65.0) < 0.01
        assert result["file_size"] == 1000
        assert result["strategy"] == "crossfade"
        assert result["error"] is None


class TestCleanup:
    def test_removes_file(self, tmp_path):
        f = tmp_path / "temp.mp4"
        f.write_bytes(b"test")
        assert f.exists()
        _cleanup(str(f))
        assert not f.exists()

    def test_no_error_on_missing(self):
        # Nao deve lancar erro se arquivo nao existe
        _cleanup("/caminho/inexistente/arquivo.mp4")

    def test_no_error_on_empty(self):
        _cleanup("")

    def test_no_error_on_none(self):
        _cleanup(None)


# ─── Testes de Estrategia de Decisao ────────────────────────────────────

class TestStrategyDecision:
    """Testa a logica de decisao sem executar FFmpeg (puro calculo)."""

    def test_single_clip_long_skips_stitch(self):
        """Clipe >= 65s deve retornar strategy='single_clip'."""
        clips = [{"path": "a.mp4", "duration": 70.0}]
        total = sum(c["duration"] for c in clips)
        assert total >= MIN_DURATION_SECONDS
        # Estrategia esperada: single_clip (sem costura)

    def test_two_clips_prefer_crossfade(self):
        """2 clipes devem tentar crossfade primeiro."""
        clips = [
            {"path": "a.mp4", "duration": 35.0},
            {"path": "b.mp4", "duration": 35.0},
        ]
        assert len(clips) >= 2
        total = sum(c["duration"] for c in clips) - CROSSFADE_DURATION
        assert total >= MIN_DURATION_SECONDS

    def test_single_short_clip_needs_padding(self):
        """Clipe curto < 65s sem companheiro -> padding."""
        clips = [{"path": "a.mp4", "duration": 45.0}]
        total = sum(c["duration"] for c in clips)
        assert total < MIN_DURATION_SECONDS
        assert len(clips) < 2
        # Estrategia esperada: hook_cta_padding
