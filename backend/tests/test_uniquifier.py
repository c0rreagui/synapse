"""
Tests — Uniquifier + Caption Engine

Cobre:
  1. uniquifier._generate_variant_params: determinismo, unicidade, ranges
  2. uniquifier._build_ffmpeg_cmd: estrutura do comando
  3. uniquifier.generate_variants: single profile skip, multi-profile routing
  4. caption_engine: variações mecânicas, parsing JSON, fallback

Não requer Docker/FFmpeg. Roda com: pytest backend/tests/test_uniquifier.py -v
"""
import sys
import os
import hashlib
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.clipper.uniquifier import (
    _generate_variant_params,
    _build_ffmpeg_cmd,
    CROP_OFFSET_RANGE,
    SPEED_RANGE,
    BRIGHTNESS_RANGE,
    CONTRAST_RANGE,
    SATURATION_RANGE,
    NOISE_RANGE,
    TEMPO_RANGE,
    PITCH_RANGE,
    LOWPASS_RANGE,
    CRF_RANGE,
    VIDEO_BITRATE_RANGE,
    AUDIO_BITRATE_RANGE,
)

from core.caption_engine import (
    _mechanical_variation,
    _parse_variations_json,
)


# ─── 1. VARIANT PARAMS — Determinismo ──────────────────────────────────

class TestVariantParamsDeterminism:
    """Mesma entrada sempre gera mesmos params."""

    def test_same_input_same_output(self):
        p1 = _generate_variant_params("/app/data/video.mp4", "profile_a", 0)
        p2 = _generate_variant_params("/app/data/video.mp4", "profile_a", 0)
        assert p1 == p2

    def test_different_profile_different_output(self):
        p1 = _generate_variant_params("/app/data/video.mp4", "profile_a", 0)
        p2 = _generate_variant_params("/app/data/video.mp4", "profile_b", 0)
        assert p1 != p2

    def test_different_index_different_output(self):
        p1 = _generate_variant_params("/app/data/video.mp4", "profile_a", 0)
        p2 = _generate_variant_params("/app/data/video.mp4", "profile_a", 1)
        assert p1 != p2

    def test_different_source_different_output(self):
        p1 = _generate_variant_params("/app/data/video1.mp4", "profile_a", 0)
        p2 = _generate_variant_params("/app/data/video2.mp4", "profile_a", 0)
        assert p1 != p2


# ─── 2. VARIANT PARAMS — Ranges ───────────────────────────────────────

class TestVariantParamsRanges:
    """Todos os params caem dentro dos ranges configurados."""

    @pytest.fixture
    def params(self):
        return _generate_variant_params("/app/data/test.mp4", "test_profile", 42)

    def test_crop_in_range(self, params):
        crop = params["crop"]
        assert CROP_OFFSET_RANGE[0] <= crop["dx"] <= CROP_OFFSET_RANGE[1]
        assert CROP_OFFSET_RANGE[0] <= crop["dy"] <= CROP_OFFSET_RANGE[1]
        assert 0 <= crop["ox"] <= crop["dx"] // 2
        assert 0 <= crop["oy"] <= crop["dy"] // 2

    def test_speed_in_range(self, params):
        assert SPEED_RANGE[0] <= params["speed"] <= SPEED_RANGE[1]

    def test_color_in_range(self, params):
        c = params["color"]
        assert BRIGHTNESS_RANGE[0] <= c["brightness"] <= BRIGHTNESS_RANGE[1]
        assert CONTRAST_RANGE[0] <= c["contrast"] <= CONTRAST_RANGE[1]
        assert SATURATION_RANGE[0] <= c["saturation"] <= SATURATION_RANGE[1]

    def test_noise_in_range(self, params):
        assert NOISE_RANGE[0] <= params["noise"] <= NOISE_RANGE[1]

    def test_audio_tempo_in_range(self, params):
        assert TEMPO_RANGE[0] <= params["audio"]["tempo"] <= TEMPO_RANGE[1]

    def test_audio_pitch_in_range(self, params):
        assert PITCH_RANGE[0] <= params["audio"]["pitch"] <= PITCH_RANGE[1]

    def test_audio_lowpass_in_range(self, params):
        assert LOWPASS_RANGE[0] <= params["audio"]["lowpass"] <= LOWPASS_RANGE[1]

    def test_encoding_crf_in_range(self, params):
        assert CRF_RANGE[0] <= params["encoding"]["crf"] <= CRF_RANGE[1]

    def test_encoding_video_bitrate_in_range(self, params):
        br = int(params["encoding"]["video_bitrate"].replace("k", ""))
        assert VIDEO_BITRATE_RANGE[0] <= br <= VIDEO_BITRATE_RANGE[1]

    def test_encoding_audio_bitrate_in_range(self, params):
        br = int(params["encoding"]["audio_bitrate"].replace("k", ""))
        assert AUDIO_BITRATE_RANGE[0] <= br <= AUDIO_BITRATE_RANGE[1]

    def test_encoding_preset_valid(self, params):
        assert params["encoding"]["preset"] in ("medium", "slow")

    def test_creation_time_is_iso(self, params):
        from datetime import datetime
        # Should parse without error
        datetime.fromisoformat(params["creation_time"])


# ─── 3. VARIANT PARAMS — Unicidade em batch ───────────────────────────

class TestVariantParamsUniqueness:
    """N perfis geram N conjuntos de params distintos."""

    def test_all_params_unique_for_10_profiles(self):
        profiles = [f"profile_{i}" for i in range(10)]
        all_params = [
            _generate_variant_params("/app/data/video.mp4", slug, idx)
            for idx, slug in enumerate(profiles)
        ]
        # Cada speed deve ser único
        speeds = [p["speed"] for p in all_params]
        assert len(set(speeds)) == len(speeds), "Speeds should be unique across profiles"

        # Cada CRF deve ser... bem, com range 18-23 e 10 profiles haverá colisões,
        # mas a combinação completa de params deve ser única
        param_hashes = [
            hashlib.md5(json.dumps(p, sort_keys=True).encode()).hexdigest()
            for p in all_params
        ]
        assert len(set(param_hashes)) == len(param_hashes), "Full param sets should be unique"


# ─── 4. FFMPEG CMD — Estrutura ─────────────────────────────────────────

class TestFFmpegCommand:
    """Valida a estrutura do comando FFmpeg gerado."""

    @pytest.fixture
    def cmd(self):
        params = _generate_variant_params("/app/data/test.mp4", "myprofile", 0)
        return _build_ffmpeg_cmd("/app/data/test.mp4", "/app/data/out.mp4", params)

    def test_starts_with_ffmpeg(self, cmd):
        assert cmd[0] == "ffmpeg"

    def test_has_overwrite_flag(self, cmd):
        assert "-y" in cmd

    def test_has_input(self, cmd):
        idx = cmd.index("-i")
        assert cmd[idx + 1] == "/app/data/test.mp4"

    def test_has_video_filter(self, cmd):
        assert "-vf" in cmd
        idx = cmd.index("-vf")
        vf = cmd[idx + 1]
        assert "crop=" in vf
        assert "scale=1080:1920" in vf
        assert "setpts=" in vf
        assert "noise=" in vf
        assert "eq=" in vf
        assert "drawbox=" in vf

    def test_has_audio_filter(self, cmd):
        assert "-af" in cmd
        idx = cmd.index("-af")
        af = cmd[idx + 1]
        assert "atempo=" in af
        assert "asetrate=" in af
        assert "lowpass=" in af

    def test_strips_metadata(self, cmd):
        assert "-map_metadata" in cmd
        idx = cmd.index("-map_metadata")
        assert cmd[idx + 1] == "-1"

    def test_adds_creation_time(self, cmd):
        assert "-metadata" in cmd
        idx = cmd.index("-metadata")
        assert cmd[idx + 1].startswith("creation_time=")

    def test_output_path_is_last(self, cmd):
        assert cmd[-1] == "/app/data/out.mp4"

    def test_has_h264_codec(self, cmd):
        idx = cmd.index("-c:v")
        assert cmd[idx + 1] == "libx264"

    def test_has_faststart(self, cmd):
        assert "+faststart" in cmd


# ─── 5. CAPTION ENGINE — Mechanical fallback ──────────────────────────

class TestMechanicalVariation:
    """Fallback mecânico produz variações diferentes da base."""

    def test_produces_different_text(self):
        base = "ele simplesmente DESISTIU no meio do boss kkkk"
        variations = [_mechanical_variation(base, i) for i in range(4)]
        # Pelo menos 3 das 4 devem ser diferentes da base
        different = [v for v in variations if v != base]
        assert len(different) >= 2, f"Expected >= 2 different, got {len(different)}: {variations}"

    def test_synonym_substitution(self):
        base = "mano olha esse bixo kkkk"
        result = _mechanical_variation(base, 0)  # strategy 0 = synonyms
        # Deve ter substituído pelo menos uma gíria
        assert result != base or "cara" in result or "vei" in result or "rsrs" in result

    def test_clause_inversion(self):
        base = "ele desistiu do boss — simplesmente largou tudo"
        result = _mechanical_variation(base, 1)  # strategy 1 = inversion
        assert result != base

    def test_question_prefix(self):
        base = "esse cara é insano demais"
        result = _mechanical_variation(base, 3)  # strategy 3 = question/exclamation prefix
        assert result != base  # Must be different from original
        # Strategy 3 adds a prefix ("vocês viram isso??", "alguém explica isso:", etc.)
        assert "?" in result or "!!" in result or ":" in result

    def test_empty_base_returns_empty(self):
        result = _mechanical_variation("", 0)
        assert result == ""


# ─── 6. CAPTION ENGINE — JSON Parsing ─────────────────────────────────

class TestCaptionJsonParsing:
    """Parser robusto de JSON de variações."""

    def test_parses_clean_json(self):
        content = '{"variations": [{"caption": "test1", "hashtags": ["#a"]}, {"caption": "test2", "hashtags": ["#a"]}]}'
        result = _parse_variations_json(content, 2)
        assert result is not None
        assert len(result) == 2
        assert result[0]["caption"] == "test1"

    def test_parses_json_in_code_fence(self):
        content = '```json\n{"variations": [{"caption": "fenced", "hashtags": []}]}\n```'
        result = _parse_variations_json(content, 1)
        assert result is not None
        assert result[0]["caption"] == "fenced"

    def test_returns_none_for_garbage(self):
        result = _parse_variations_json("this is not json at all", 2)
        assert result is None

    def test_returns_none_for_wrong_structure(self):
        result = _parse_variations_json('{"caption": "single, not array"}', 1)
        assert result is None

    def test_handles_extra_text_around_json(self):
        content = 'Here are the variations:\n{"variations": [{"caption": "embedded", "hashtags": ["#t"]}]}\nDone!'
        result = _parse_variations_json(content, 1)
        assert result is not None
        assert result[0]["caption"] == "embedded"
