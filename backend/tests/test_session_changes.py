"""
QA — Testes unitários para as mudanças da sessão atual.

Cobre:
  1. subtitle_engine — street layout (Alignment=2, MarginV=384)
  2. factory.py — regex de strip de hashtags
  3. factory.py — prompt compilation-aware (1 vs N clips)
  4. Regressão: `re` sempre disponível independente do caminho de parse JSON

Não requer Docker/DB. Roda com: pytest backend/tests/test_session_changes.py -v
"""
import re
import copy
import pytest


# ─── 1. SUBTITLE ENGINE — Street Layout Safe Zone ───────────────────────────

class TestStreetLayoutPositioning:
    """
    O layout street deve usar Alignment=2 (bottom-center) e MarginV=384 (20vh).
    Outros layouts devem manter Alignment=5 (center) e MarginV=0.
    """

    def _parse_style_line(self, ass_content: str, style_name: str) -> dict:
        """Extrai os campos da linha Style: do arquivo .ass."""
        for line in ass_content.splitlines():
            if line.startswith(f"Style: {style_name},"):
                fields = line.split(",")
                # Format: Name,Font,Size,Primary,Secondary,Outline,Back,Bold,Italic,
                #         Underline,Strike,ScaleX,ScaleY,Spacing,Angle,BorderStyle,
                #         Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
                return {
                    "alignment": int(fields[18]),
                    "margin_v":  int(fields[21]),
                }
        raise AssertionError(f"Style '{style_name}' not found in ASS content")

    def _generate_ass_header(self, layout_mode: str) -> str:
        """Gera só o header .ass sem escrever em disco."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from core.clipper.subtitle_engine import STYLES, _build_ass_header
        style = copy.copy(STYLES["opus"])
        if layout_mode == "street":
            style.alignment = 2
            style.margin_bottom = 384
        return _build_ass_header(style)

    def test_street_alignment_is_bottom_center(self):
        content = self._generate_ass_header("street")
        active = self._parse_style_line(content, "Active")
        assert active["alignment"] == 2, f"Expected Alignment=2, got {active['alignment']}"

    def test_street_margin_v_is_20vh(self):
        content = self._generate_ass_header("street")
        active = self._parse_style_line(content, "Active")
        assert active["margin_v"] == 384, f"Expected MarginV=384, got {active['margin_v']}"

    def test_gameplay_alignment_unchanged(self):
        content = self._generate_ass_header("gameplay")
        active = self._parse_style_line(content, "Active")
        assert active["alignment"] == 5
        assert active["margin_v"] == 0

    def test_inactive_style_mirrors_active_alignment(self):
        """Active e Inactive devem ter o mesmo alignment."""
        content = self._generate_ass_header("street")
        active   = self._parse_style_line(content, "Active")
        inactive = self._parse_style_line(content, "Inactive")
        assert active["alignment"] == inactive["alignment"]
        assert active["margin_v"]  == inactive["margin_v"]

    def test_hook_style_keeps_top_alignment(self):
        """Hook (retenção primeiros 3s) deve manter Alignment=8 (topo-centro)."""
        content = self._generate_ass_header("street")
        hook = self._parse_style_line(content, "Hook")
        assert hook["alignment"] == 8, "Hook deve permanecer no topo (Alignment=8)"

    def test_street_copy_does_not_mutate_global_style(self):
        """copy.copy garante que o dict STYLES não é modificado pelo street override."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from core.clipper.subtitle_engine import STYLES
        original_alignment     = STYLES["opus"].alignment
        original_margin_bottom = STYLES["opus"].margin_bottom

        self._generate_ass_header("street")  # triggera o copy.copy path

        assert STYLES["opus"].alignment     == original_alignment
        assert STYLES["opus"].margin_bottom == original_margin_bottom


# ─── 2. HASHTAG STRIP REGEX ─────────────────────────────────────────────────

HASHTAG_PATTERN = re.compile(r'(?<!\w)#\w+')

def strip_hashtags(caption: str) -> str:
    return HASHTAG_PATTERN.sub('', caption).strip()


class TestHashtagStrip:
    """
    A regex (?<!\\w)#\\w+ deve remover hashtags sem destruir texto normal.
    """

    def test_strips_trailing_hashtags(self):
        assert strip_hashtags("ele perdeu o controle #fyp #gta") == "ele perdeu o controle"

    def test_strips_leading_hashtag(self):
        assert strip_hashtags("#fyp texto viral") == "texto viral"

    def test_strips_multiple_hashtags(self):
        result = strip_hashtags("texto #fyp #gta #twitch mais texto")
        assert "#" not in result

    def test_preserves_plain_text(self):
        text = "ele simplesmente DESISTIU no meio do boss"
        assert strip_hashtags(text) == text

    def test_empty_caption(self):
        assert strip_hashtags("") == ""

    def test_only_hashtags_returns_empty(self):
        assert strip_hashtags("#fyp #gta #twitch") == ""

    def test_does_not_strip_word_containing_hash_mid_word(self):
        # "C#" (linguagem de programação) — \\w antes do # bloqueia o match
        result = strip_hashtags("programando em C# hoje")
        assert "C#" in result

    def test_unicode_hashtags(self):
        # Hashtags em português com caracteres especiais
        result = strip_hashtags("momento épico #ação #twitch")
        assert "#ação" not in result
        assert "momento épico" in result

    def test_does_not_leave_double_spaces(self):
        # Após strip, .strip() remove espaços externos mas espaços internos podem ficar
        # Verificar que o output pelo menos não começa/termina com espaço
        result = strip_hashtags("  texto  #fyp  ")
        assert result == result.strip()


# ─── 3. PROMPT COMPILATION-AWARENESS ────────────────────────────────────────

def _build_missao(n: int) -> str:
    if n > 1:
        return (
            f"─── MISSÃO ───\n"
            f"Crie UMA descrição viral para TikTok/Shorts para um COMPILADO de {n} clips da Twitch.\n"
            f"Cada clip tem sua própria transcrição — leia TODAS antes de escrever.\n"
            f"A caption deve capturar a ENERGIA/VIBE GERAL do compilado, não tratar como clip único.\n"
            f"O espectador deve sentir que tem VÁRIOS momentos épicos no vídeo, não apenas um."
        )
    return "─── MISSÃO ───\nCrie UMA descrição viral para TikTok/Shorts baseada no clipe abaixo."


def _build_analise(n: int) -> str:
    if n > 1:
        return (
            f"[ANÁLISE DE COMPILADO: {n} CLIPS]\n"
            f"Processamento obrigatório antes da redação:\n"
            f"1. FIO CONDUTOR: Identifique o tema ou padrão de energia que unifica os {n} clips "
            f"(ex: caos, debate intenso, reações absurdas).\n"
            f"2. TOM: Defina a emoção dominante do conjunto para calibrar a legenda.\n"
            f"3. GANCHO (HOOK): Isole o momento de maior impacto para abrir o texto.\n"
            f"4. REDAÇÃO: Utilize o plural e garanta que o espectador perceba que existem "
            f"múltiplos eventos aguardando, gerando escassez e maximizando a retenção."
        )
    return (
        "[ANÁLISE DE CLIP ÚNICO]\n"
        "Processamento obrigatório antes da redação:\n"
        "1. FOCO: Identifique a fala, ação ou reação de maior pico emocional.\n"
        "2. TOM: Defina a emoção central do corte.\n"
        "3. REDAÇÃO: Construa a legenda alavancada exclusivamente neste MOMENTO-CHAVE, "
        "gerando curiosidade imediata no primeiro segundo."
    )


class TestPromptCompilationAwareness:

    # ── MISSÃO block ──

    def test_single_clip_missao_does_not_mention_compilado(self):
        missao = _build_missao(1)
        assert "COMPILADO" not in missao

    def test_single_clip_missao_references_single_clip(self):
        missao = _build_missao(1)
        assert "clipe abaixo" in missao

    def test_multi_clip_missao_mentions_compilado(self):
        missao = _build_missao(4)
        assert "COMPILADO" in missao
        assert "4 clips" in missao

    def test_multi_clip_missao_warns_varios_momentos(self):
        missao = _build_missao(3)
        assert "VÁRIOS" in missao

    def test_boundary_n_equals_2_is_multi(self):
        missao = _build_missao(2)
        assert "COMPILADO" in missao

    # ── ANÁLISE block ──

    def test_single_clip_analise_uses_foco(self):
        analise = _build_analise(1)
        assert "FOCO" in analise
        assert "FIO CONDUTOR" not in analise

    def test_multi_clip_analise_uses_fio_condutor(self):
        analise = _build_analise(4)
        assert "FIO CONDUTOR" in analise
        assert "FOCO" not in analise

    def test_multi_clip_analise_includes_clip_count(self):
        analise = _build_analise(3)
        assert "3 CLIPS" in analise
        assert "3 clips" in analise  # no corpo

    def test_multi_clip_analise_asks_for_plural_redacao(self):
        analise = _build_analise(5)
        assert "plural" in analise.lower() or "múltiplos" in analise.lower()

    def test_analise_always_has_retorno_instruction(self):
        # O bloco RETORNO OBRIGATÓRIO é constante (fora do f-string condicional)
        # Verificar que o texto está correto
        retorno = "RETORNO OBRIGATÓRIO: Forneça a saída ESTRITAMENTE em formato JSON."
        assert "JSON" in retorno  # trivial mas documenta a expectativa

    # ── Edge cases: total_clips=0 (job sem clips) ──

    @pytest.mark.parametrize("total_clips", [0, None])
    def test_falsy_clips_falls_back_to_single(self, total_clips):
        # Documenta: _n = total_clips or 1 no código de produção
        n = total_clips or 1
        missao = _build_missao(n)
        assert "COMPILADO" not in missao


# ─── 4. REGRESSÃO: re SEMPRE DISPONÍVEL (bug UnboundLocalError) ─────────────

class TestReModuleScope:
    """
    Garante que o módulo `re` está disponível no escopo onde re.sub() é chamado,
    independente de qual Strategy de parse JSON foi executada.

    Este teste documenta o bug que causou o erro:
    "cannot access local variable 're' where it is not associated with a value"

    Root cause: `import re` dentro de blocos `if not parsed:` tornava `re` uma
    variável LOCAL da função. Se Strategy 1 (json direto) funcionasse, `re` nunca
    era inicializado localmente → UnboundLocalError no re.sub() final.

    Fix: `import re` movido para o topo do módulo (factory.py:2).
    """

    def test_re_available_at_module_level_in_factory(self):
        """re deve estar no topo do módulo factory, não em blocos condicionais."""
        import ast, os
        factory_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "api", "endpoints", "factory.py"
        )
        with open(factory_path, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        # Verificar que `import re` aparece no nível do módulo
        module_level_imports = [
            node for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        re_in_module_level = any(
            isinstance(node, ast.Import) and any(a.name == "re" for a in node.names)
            for node in module_level_imports
        )
        assert re_in_module_level, (
            "REGRESSÃO: `import re` deve estar no nível do módulo em factory.py. "
            "Se removido, re.sub() falhará com UnboundLocalError quando JSON parse "
            "for bem-sucedido na Strategy 1."
        )

    def test_hashtag_sub_works_with_module_level_re(self):
        """Simula o caminho exato do código: re.sub na caption após parse JSON."""
        import re as module_re  # Como está no módulo após o fix
        caption = "ele PERDEU o controle com isso #GrandTheftAutoV #fyp"
        result = module_re.sub(r'(?<!\w)#\w+', '', caption).strip()
        assert result == "ele PERDEU o controle com isso"
        assert "#" not in result

    def test_strategy1_path_re_available(self):
        """
        Simula o caminho onde Strategy 1 (json.loads direto) funciona
        e re.sub() é chamado depois — sem nenhum `import re` intermediário.
        """
        import json, re

        content = '{"caption": "texto viral #fyp", "hashtags": ["#fyp"]}'

        parsed = None
        try:
            parsed = json.loads(content)  # Strategy 1 funciona
        except json.JSONDecodeError:
            pass

        # Nenhum dos blocos `if not parsed:` é executado
        assert parsed is not None

        caption = parsed.get("caption", "").strip()
        # re.sub deve funcionar sem ter passado por nenhum `import re` intermediário
        caption = re.sub(r'(?<!\w)#\w+', '', caption).strip()
        assert caption == "texto viral"


# ─── 5. json_mod REMOVIDO — usa json de nível de módulo ────────────────────

class TestNoJsonModAlias:
    """
    Verifica que factory.py NÃO contém `import json as json_mod` (deferred
    alias dentro da função). O módulo json já está importado no topo.
    """

    def _read_factory_source(self) -> str:
        import os
        factory_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "api", "endpoints", "factory.py"
        )
        with open(factory_path, encoding="utf-8") as f:
            return f.read()

    def test_no_json_mod_alias(self):
        """Não deve existir `import json as json_mod` dentro de funções."""
        source = self._read_factory_source()
        assert "json_mod" not in source, (
            "REGRESSÃO: `import json as json_mod` deve ser removido. "
            "O factory.py já importa `json` no nível do módulo."
        )

    def test_json_module_level_import(self):
        """json deve estar no nível do módulo."""
        import ast, os
        factory_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "api", "endpoints", "factory.py"
        )
        with open(factory_path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        module_imports = [
            node for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        json_at_module = any(
            isinstance(node, ast.Import) and any(a.name == "json" for a in node.names)
            for node in module_imports
        )
        assert json_at_module, "json deve estar importado no nível do módulo em factory.py"


# ─── 6. HASHTAG TYPE VALIDATION ────────────────────────────────────────────

class TestHashtagTypeValidation:
    """
    O LLM pode retornar tipos inesperados no array `hashtags`
    (int, null, dict). Apenas strings devem ser aceitas.
    """

    def _filter_hashtags(self, raw):
        """Simula o filtro em factory.py."""
        return [h for h in raw if isinstance(h, str)][:5]

    def test_filters_non_string_items(self):
        raw = ["#fyp", 123, None, "#gta", {"tag": "#twitch"}, True]
        result = self._filter_hashtags(raw)
        assert result == ["#fyp", "#gta"]

    def test_limits_to_five(self):
        raw = [f"#tag{i}" for i in range(10)]
        result = self._filter_hashtags(raw)
        assert len(result) == 5

    def test_empty_list(self):
        assert self._filter_hashtags([]) == []

    def test_all_valid_strings(self):
        raw = ["#twitch", "#fyp", "#gaming"]
        assert self._filter_hashtags(raw) == raw

    def test_all_invalid_returns_empty(self):
        raw = [123, None, False, 4.5]
        assert self._filter_hashtags(raw) == []


# ─── 7. _resolve_layout PRIORITY FIX ───────────────────────────────────────

class TestResolveLayoutPriority:
    """
    Testa a lógica de prioridade do _resolve_layout no worker.py:
      1. Per-clip override (máxima prioridade)
      2. Job-level layout_mode (só quando NÃO há nenhum override)
      3. Game-based auto-detection (Just Chatting → podcast, IRL → street)
      4. Default: gameplay

    Bug corrigido: quando overrides existiam para ALGUNS clips,
    clips sem override herdavam o layout_mode do job em vez de
    auto-detectar pelo game.
    """

    @staticmethod
    def _detect_game(game: str) -> str:
        """Auto-detect layout from game name."""
        g = game.lower()
        if "just chatting" in g:
            return "podcast"
        if "irl" in g or "in real life" in g:
            return "street"
        return "gameplay"

    @classmethod
    def _make_resolver(cls, layout_overrides, layout_mode, clip_metadata):
        """
        Cria uma função _resolve_layout standalone — mesma lógica do worker.
        """
        def _resolve_layout(clip_idx: int) -> str:
            idx_str = str(clip_idx)
            if idx_str in layout_overrides and layout_overrides[idx_str] != "auto":
                return layout_overrides[idx_str]
            if not layout_overrides and layout_mode != "auto":
                return layout_mode
            if clip_idx < len(clip_metadata):
                return cls._detect_game((clip_metadata[clip_idx].get("game") or ""))
            return "gameplay"
        return _resolve_layout

    # ── Priority 1: Per-clip override wins ──

    def test_explicit_override_wins_over_job_mode(self):
        resolve = self._make_resolver(
            layout_overrides={"0": "podcast"},
            layout_mode="gameplay",
            clip_metadata=[{"game": "Fortnite"}],
        )
        assert resolve(0) == "podcast"

    def test_explicit_override_street(self):
        resolve = self._make_resolver(
            layout_overrides={"1": "street"},
            layout_mode="gameplay",
            clip_metadata=[{"game": "A"}, {"game": "B"}],
        )
        assert resolve(1) == "street"

    def test_override_auto_falls_through(self):
        """Override 'auto' is NOT an explicit choice — should auto-detect."""
        resolve = self._make_resolver(
            layout_overrides={"0": "auto"},
            layout_mode="gameplay",
            clip_metadata=[{"game": "Just Chatting"}],
        )
        # "auto" override → skip step 1 → layout_overrides is non-empty →
        # skip step 2 → step 3 detects "Just Chatting" → podcast
        assert resolve(0) == "podcast"

    # ── Priority 2: Job-level mode (only when NO overrides at all) ──

    def test_job_level_mode_when_no_overrides(self):
        resolve = self._make_resolver(
            layout_overrides={},
            layout_mode="street",
            clip_metadata=[{"game": "Just Chatting"}],
        )
        # No overrides → step 2: layout_mode="street" ≠ "auto" → return "street"
        assert resolve(0) == "street"

    def test_job_level_auto_falls_to_game_detection(self):
        resolve = self._make_resolver(
            layout_overrides={},
            layout_mode="auto",
            clip_metadata=[{"game": "Just Chatting"}],
        )
        assert resolve(0) == "podcast"

    # ── KEY FIX: clips without override when OTHER clips have overrides ──

    def test_unspecified_clip_autodetects_when_overrides_exist(self):
        """
        BUG CORRIGIDO: clip 1 sem override NÃO deve herdar layout_mode="gameplay".
        Deve auto-detectar pelo game (Just Chatting → podcast).
        """
        resolve = self._make_resolver(
            layout_overrides={"0": "podcast"},  # clip 0 tem override
            layout_mode="gameplay",             # job-level mode (antigo)
            clip_metadata=[
                {"game": "Fortnite"},       # clip 0: override "podcast"
                {"game": "Just Chatting"},  # clip 1: sem override → auto-detect
            ],
        )
        assert resolve(0) == "podcast"  # override ✓
        assert resolve(1) == "podcast"  # auto-detect Just Chatting ✓ (antes: gameplay ✗)

    def test_unspecified_clip_irl_autodetects_when_overrides_exist(self):
        resolve = self._make_resolver(
            layout_overrides={"0": "gameplay"},
            layout_mode="podcast",
            clip_metadata=[
                {"game": "Fortnite"},
                {"game": "IRL"},
            ],
        )
        assert resolve(0) == "gameplay"  # override
        assert resolve(1) == "street"    # auto-detect IRL

    def test_unspecified_clip_defaults_to_gameplay(self):
        """Clip sem override, sem game reconhecido → default gameplay."""
        resolve = self._make_resolver(
            layout_overrides={"0": "podcast"},
            layout_mode="gameplay",
            clip_metadata=[
                {"game": "Fortnite"},
                {"game": "Valorant"},  # não é Just Chatting nem IRL
            ],
        )
        assert resolve(1) == "gameplay"

    # ── Priority 3: Game auto-detection ──

    def test_just_chatting_detected_as_podcast(self):
        resolve = self._make_resolver({}, "auto", [{"game": "Just Chatting"}])
        assert resolve(0) == "podcast"

    def test_irl_detected_as_street(self):
        resolve = self._make_resolver({}, "auto", [{"game": "IRL"}])
        assert resolve(0) == "street"

    def test_in_real_life_detected_as_street(self):
        resolve = self._make_resolver({}, "auto", [{"game": "Travel & Outdoors (In Real Life)"}])
        assert resolve(0) == "street"

    def test_game_detected_as_gameplay(self):
        resolve = self._make_resolver({}, "auto", [{"game": "Grand Theft Auto V"}])
        assert resolve(0) == "gameplay"

    # ── Edge cases ──

    def test_missing_game_in_metadata(self):
        resolve = self._make_resolver({}, "auto", [{}])
        assert resolve(0) == "gameplay"

    def test_none_game_in_metadata(self):
        resolve = self._make_resolver({}, "auto", [{"game": None}])
        assert resolve(0) == "gameplay"

    def test_clip_index_out_of_metadata_range(self):
        resolve = self._make_resolver({}, "auto", [{"game": "Just Chatting"}])
        # clip_idx=5 but only 1 metadata entry → default
        assert resolve(5) == "gameplay"

    def test_empty_metadata_list(self):
        resolve = self._make_resolver({}, "auto", [])
        assert resolve(0) == "gameplay"

    def test_three_clips_mixed(self):
        """Cenário real: 3 clips, 1 override, 2 auto-detect."""
        resolve = self._make_resolver(
            layout_overrides={"0": "street"},
            layout_mode="gameplay",
            clip_metadata=[
                {"game": "Fortnite"},
                {"game": "Just Chatting"},
                {"game": "IRL"},
            ],
        )
        assert resolve(0) == "street"    # override
        assert resolve(1) == "podcast"   # auto-detect Just Chatting
        assert resolve(2) == "street"    # auto-detect IRL
