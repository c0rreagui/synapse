"""
Clipper Worker - ARQ Worker Settings
=====================================

Worker dedicado do ARQ para rodar o pipeline do clipper.
Isolado do worker principal (Playwright) para podermos otimizar recursos,
ja que o Whisper e o FFmpeg exigem bastante CPU/RAM (e VRAM se disponivel).

Configurado para esvaziar a fila `clipper:queue`.
"""

import sys
import logging
import os
from datetime import datetime, timezone
from arq.connections import RedisSettings
from dotenv import load_dotenv



# Carregar variaveis
load_dotenv()

# Ajustar path se necessario para rodar isolado
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.clipper.downloader import download_job_clips
from core.clipper.transcriber import transcribe_job_clips
from core.clipper.subtitle_engine import generate_ass_for_multiple
from core.clipper.editor import edit_clip
from core.clipper.stitcher import ensure_minimum_duration

from core.database import safe_session
from core.clipper.models import ClipJob, TwitchTarget
from core.models import PendingApproval

logger = logging.getLogger("ClipperWorker")

# Track job IDs enqueued during startup to prevent double-enqueue in the first orphan scan
_startup_enqueued_ids: set = set()


def _fail_job_db(job_id: int, error_message: str, current_step: str = "Falha no pipeline."):
    """Helper para marcar job como falhado no DB."""
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error_message[:500]
            job.current_step = current_step
            db.commit()
    logger.error(f"Job #{job_id} falhado: {error_message[:200]}")


async def _process_clip_job_inner(ctx, job_id: int):
    """
    Funcao principal orquestradora do pipeline de um unico ClipJob.
    1. Download dos clipes
    2. Whisper (transcricao word-level)
    3. ASS (legendas estilizadas)
    4. FFmpeg Edit (facecam crop, ass burn, 9:16)
    5. Stitcher (crossfade se multiplos clipes)
    """
    logger.info(f"==> Iniciando processamento do ClipJob #{job_id}")

    # Guard: só processar jobs que estão na fila (pending) ou em etapas intermediárias
    # NUNCA processar waiting_clips diretamente — devem ser promovidos para pending primeiro
    with safe_session() as db:
        guard_job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not guard_job:
            logger.warning(f"Job #{job_id} nao encontrado no DB, pulando.")
            return
        if guard_job.status not in ("pending", "downloading", "transcribing", "editing", "stitching"):
            logger.info(f"Job #{job_id} em status '{guard_job.status}', não pode ser processado. Deve ir para fila (pending) primeiro.")
            return

    # 1. Download
    dl_result = await download_job_clips(job_id)
    if not dl_result.get("success"):
        error_msg = dl_result.get("error", "Unknown error")
        _fail_job_db(job_id, f"Download error: {error_msg}", "Falha no download dos clipes.")
        return

    # 2. Transcricao (Whisper)
    tr_result = await transcribe_job_clips(job_id)
    if not tr_result.get("success"):
        error_msg = tr_result.get("error", "Unknown error")
        errors = tr_result.get("errors", [])
        full_error = f"Transcription error: {error_msg}" + (f" | {' | '.join(errors)}" if errors else "")
        _fail_job_db(job_id, full_error, "Falha na transcricao de audio.")
        return

    # Preparar para edicao
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if not job:
            return
        local_paths = job.clip_local_paths or []
        transcriptions = job.whisper_result or []

    if not local_paths or not transcriptions:
        _fail_job_db(job_id, "Arquivos locais ou transcricoes nao encontrados.", "Falha ao preparar para edicao.")
        return

    # Diagnóstico: rastrear mismatch entre local_paths e transcriptions
    if len(local_paths) != len(transcriptions):
        logger.warning(
            f"Job #{job_id}: MISMATCH — {len(local_paths)} local_paths vs "
            f"{len(transcriptions)} transcriptions. "
            f"zip() vai truncar para {min(len(local_paths), len(transcriptions))} clips!"
        )
    logger.info(f"Job #{job_id}: Pipeline input — {len(local_paths)} clips, {len(transcriptions)} transcrições")

    # Incluir todos os clips (clips sem palavras são editados sem legendas)
    valid_pairs = list(zip(local_paths, transcriptions))
    wordless = [p for p, t in valid_pairs if t.get("word_count", 0) == 0]
    if wordless:
        logger.info(f"Job #{job_id}: {len(wordless)} clip(s) sem palavras — serão editados sem legendas.")

    if not valid_pairs:
        _fail_job_db(job_id, "Nenhum clipe encontrado para edição.", "Falha: lista de clips vazia.")
        return

    # Buscar dados principais em uma única transação
    channel_name = None
    target_auto_approve = False
    target_id = None
    target_type = "channel"
    layout_mode = "auto"
    clip_titles = []
    clip_metadata = []
    layout_overrides = {}

    with safe_session() as db:
        job_obj = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job_obj:
            clip_metadata = job_obj.clip_metadata or []
            layout_overrides = job_obj.layout_mode_overrides or {}
            layout_mode = getattr(job_obj, 'layout_mode', 'auto') or 'auto'
            
            # Extrair títulos dos clips para metadados ricos
            clip_titles = [meta.get("title", "") for meta in clip_metadata]

            if job_obj.target_id:
                target_id = job_obj.target_id
                target = db.query(TwitchTarget).filter(TwitchTarget.id == job_obj.target_id).first()
                if target:
                    channel_name = target.channel_name
                    target_type = getattr(target, 'target_type', 'channel') or 'channel'
                    target_auto_approve = getattr(target, 'auto_approve', False) or False
                    # Para targets de categoria, extrair o nome do streamer real do metadata
                    if target_type == "category" and clip_metadata:
                        real_streamer = clip_metadata[0].get("broadcaster_name")
                        if real_streamer:
                            channel_name = real_streamer

            # Atualiza DB para "editing"
            job_obj.status = "editing"
            job_obj.current_step = f"Editando 0/{len(valid_pairs)} clipes..."
            job_obj.progress_pct = 50
            db.commit()

    # 3. Gerar ASS & 4. FFmpeg Edit (por clipe individual)
    edited_paths = []

    # ── Anti-Shadowban: gerar params UMA VEZ por job (consistência entre clips) ──
    import random as _random
    from core.clipper.editor import generate_asb_params
    asb_params = generate_asb_params()

    # Estilo de legenda sorteado por job (variabilidade visual entre vídeos)
    asb_style = _random.choice(["opus", "neon", "cyan"])

    logger.info(
        f"Job #{job_id} ASB: speed={asb_params['speed']}x, "
        f"grain={asb_params['grain']}, color={asb_params['color_idx']}, "
        f"ratio={asb_params['facecam_ratio']:.0%}/{asb_params['gameplay_ratio']:.0%}, "
        f"subtitle_style={asb_style}"
    )

    # Resolver layout_mode efetivo para cada clip usando dados em memória
    def _resolve_layout(clip_idx: int) -> str:
        """Resolve layout_mode: auto → baseado no game do clip metadata (com overrides).

        Priority:
          1. Per-clip override (layout_mode_overrides[str(clip_idx)])
          2. Job-level layout_mode — only when NO per-clip overrides exist at all
             (if overrides exist for other clips, unspecified clips fall to auto-detect)
          3. Game-based auto-detection from clip metadata
          4. Default: gameplay
        """
        # 1. Override específico pro clipe
        idx_str = str(clip_idx)
        if idx_str in layout_overrides and layout_overrides[idx_str] != "auto":
            return layout_overrides[idx_str]

        # 2. Job-level mode — only honoured when there are NO per-clip overrides at all.
        # When at least one clip has an explicit override, unspecified clips fall through
        # to game-based auto-detection instead of inheriting the (possibly stale) job mode.
        if not layout_overrides and layout_mode != "auto":
            return layout_mode

        # 3. Detectar pelo metadata (game) do clip
        if clip_idx < len(clip_metadata):
            game = (clip_metadata[clip_idx].get("game") or "").lower()
            if "just chatting" in game:
                return "podcast"
            if "irl" in game or "in real life" in game:
                return "street"

        return "gameplay"  # default: split facecam + gameplay

    for idx, (path, trans) in enumerate(valid_pairs):
        ass_path = None
        clip_layout = _resolve_layout(idx)
        clip_title = clip_titles[idx] if idx < len(clip_titles) else None
        try:
            # Hook textual: título do clip nos 3 primeiros seg (apenas no 1o clip do job)
            hook = clip_title if idx == 0 else None
            # Gerar legendas apenas para clips com palavras transcritas
            if trans.get("word_count", 0) > 0:
                ass_path = generate_ass_for_multiple(
                    transcriptions=[trans],
                    style_name=asb_style,
                    time_offsets=[0.0],
                    hook_title=hook,
                    layout_mode=clip_layout,
                )
            else:
                ass_path = None

            edit_res = await edit_clip(
                video_path=path,
                ass_path=ass_path,
                timeout_seconds=900,
                channel_name=channel_name,
                layout_mode=clip_layout,
                asb_params=asb_params,
                clip_title=clip_title,
            )

            if edit_res.get("success"):
                edited_paths.append(edit_res.get("output_path"))
            else:
                logger.error(f"Job #{job_id} falhou na edicao do clipe {idx}: {edit_res.get('error')}")
        except Exception as e:
            logger.error(f"Job #{job_id} excecao na edicao do clipe {idx}: {e}", exc_info=True)
        finally:
            if ass_path and os.path.exists(ass_path):
                try:
                    os.remove(ass_path)
                except OSError:
                    pass

        with safe_session() as db:
            job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if job:
                job.current_step = f"Editando {idx + 1}/{len(valid_pairs)} clipes..."
                job.progress_pct = 50 + int(((idx + 1) / len(valid_pairs)) * 40)
                db.commit()

    if not edited_paths:
        _fail_job_db(job_id, "Nenhum clipe foi editado com sucesso.", "Falha na edicao.")
        return

    # Diagnóstico: quantos clips editados com sucesso vs total
    logger.info(
        f"Job #{job_id}: Edição concluída — {len(edited_paths)}/{len(valid_pairs)} clips editados. "
        f"Paths: {[os.path.basename(p) for p in edited_paths]}"
    )

    # ── 5. Stitching + Loop-Tail Seamless ─────────────────────────────────
    # Estratégia:
    #   - Clips normalmente >= 61s (chunking garante isso via waiting_clips)
    #   - Loop-tail: crossfade end→start para replay seamless no TikTok
    #   - Fallback para jobs expirados (timeout 72h): loop + CTA para atingir 61s
    MIN_VIDEO_DURATION = 61.0
    CTA_DURATION = 5.0

    streamer_name = channel_name or ""

    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "stitching"
            job.current_step = "Aplicando costura final..."
            job.progress_pct = 85
            db.commit()

    stitch_res = await ensure_minimum_duration(edited_clips=edited_paths)

    if not stitch_res.get("success"):
        _fail_job_db(job_id, f"Stitch error: {stitch_res.get('error')}", "Falha na costura.")
        return

    # Tracking: registrar estratégia do stitcher nos metadados
    stitch_strategy = stitch_res.get("strategy", "unknown")
    if stitch_strategy != "crossfade":
        logger.warning(f"Job #{job_id}: Stitcher usou fallback '{stitch_strategy}' (não crossfade)")

    stitched_path = stitch_res.get("output_path")
    from core.clipper.stitcher import _get_duration, create_seamless_loop, _apply_loop_tail
    stitched_duration = await _get_duration(stitched_path)

    if stitched_duration < MIN_VIDEO_DURATION:
        # ── Fallback: job expirado do waiting_clips (timeout 72h) ──
        # Não tinha clips suficientes após 72h, então usamos loop + CTA
        logger.warning(
            f"Job #{job_id}: Duração {stitched_duration:.1f}s < 61s mínimo. "
            f"Aplicando loop fallback (job expirado de waiting_clips)."
        )
        loop_target = MIN_VIDEO_DURATION - CTA_DURATION  # ~56s

        with safe_session() as db:
            j = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if j:
                j.current_step = f"Loop fallback ({stitched_duration:.0f}s → {loop_target:.0f}s)..."
                j.progress_pct = 88
                db.commit()

        loop_output = stitched_path.replace(".mp4", "_looped.mp4")
        loop_res = await create_seamless_loop(
            clip_path=stitched_path,
            target_duration=loop_target,
            output_path=loop_output,
        )

        if loop_res.get("success"):
            logger.info(f"Job #{job_id}: Loop fallback criado ({stitched_duration:.1f}s → {loop_res.get('duration', 0):.1f}s)")
            if os.path.exists(stitched_path) and stitched_path != loop_output:
                try:
                    os.remove(stitched_path)
                except OSError:
                    pass
            edited_paths_for_final = [loop_output]
        else:
            logger.warning(f"Job #{job_id}: Loop fallback falhou, usando clip original")
            edited_paths_for_final = [stitched_path]

        # CTA outro (~5s) para fechar em 61s
        if streamer_name:
            try:
                from core.clipper.hook_generator import generate_outro_filler
                hook_res = await generate_outro_filler(
                    streamer=streamer_name,
                    target_duration=CTA_DURATION,
                    bg_video_path=edited_paths_for_final[0],
                )
                if hook_res.get("success"):
                    hook_path = hook_res.get("output_path")
                    if hook_path and os.path.exists(hook_path):
                        edited_paths_for_final.append(hook_path)
            except Exception as e:
                logger.error(f"Job #{job_id}: Erro no CTA outro: {e}", exc_info=True)

        stitch_res = await ensure_minimum_duration(edited_clips=edited_paths_for_final)
        if not stitch_res.get("success"):
            _fail_job_db(job_id, f"Stitch final error: {stitch_res.get('error')}", "Falha na costura final.")
            return

    else:
        # ── Clip longo (>= 61s): loop-tail para seamless replay no TikTok ──
        with safe_session() as db:
            j = db.query(ClipJob).filter(ClipJob.id == job_id).first()
            if j:
                j.current_step = "Aplicando loop-tail seamless..."
                j.progress_pct = 92
                db.commit()

        loop_tail_output = stitched_path.replace(".mp4", "_looptail.mp4")
        tail_res = await _apply_loop_tail(stitched_path, loop_tail_output)

        if tail_res.get("success"):
            logger.info(f"Job #{job_id}: Loop-tail aplicado para seamless replay.")
            if os.path.exists(stitched_path) and stitched_path != loop_tail_output:
                try:
                    os.remove(stitched_path)
                except OSError:
                    pass
            stitch_res = tail_res
        else:
            logger.warning(f"Job #{job_id}: Loop-tail falhou, mantendo original.")

    # Marcar como concluido
    output_path = stitch_res.get("output_path")
    duration = stitch_res.get("duration", 0)

    # Verify actual duration via ffprobe (result duration can be wrong after fallback)
    if output_path and os.path.exists(output_path):
        try:
            real_dur = await _get_duration(output_path)
            if abs(real_dur - duration) > 5:
                logger.warning(f"Job #{job_id}: Duração reportada ({duration:.1f}s) difere da real ({real_dur:.1f}s). Usando real.")
            duration = real_dur
        except Exception:
            pass

    # ── Limite de duração: 160s — acima disso, trim via FFmpeg ──
    MAX_OUTPUT_DURATION = 160  # 2min40s
    if duration > MAX_OUTPUT_DURATION:
        logger.warning(
            f"Job #{job_id}: Vídeo com {duration:.0f}s (>{MAX_OUTPUT_DURATION}s). "
            f"Trimming para {MAX_OUTPUT_DURATION}s."
        )
        trimmed_path = output_path.replace(".mp4", "_trimmed.mp4")
        try:
            import subprocess
            trim_cmd = [
                "ffmpeg", "-y", "-i", output_path,
                "-t", str(MAX_OUTPUT_DURATION),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                trimmed_path,
            ]
            proc = subprocess.run(trim_cmd, capture_output=True, timeout=60)
            if proc.returncode == 0 and os.path.exists(trimmed_path):
                os.remove(output_path)
                os.rename(trimmed_path, output_path)
                duration = await _get_duration(output_path)
                logger.info(f"Job #{job_id}: Trimmed para {duration:.1f}s")
            else:
                logger.error(f"Job #{job_id}: FFmpeg trim falhou")
                _fail_job_db(job_id, f"Trim failed for {duration:.0f}s video", "Falha no trim")
                return
        except Exception as e:
            logger.error(f"Job #{job_id}: Erro no trim: {e}")
            _fail_job_db(job_id, f"Trim error: {e}", "Falha no trim")
            return

    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "completed"
            job.current_step = "Concluido!"
            job.progress_pct = 100
            job.output_path = output_path
            job.completed_at = datetime.now(timezone.utc)
            job.duration_seconds = duration
            # Registrar estratégia do stitcher e ASB params nos metadados
            pipeline_meta = {
                "stitch_strategy": stitch_strategy,
                "asb_speed": asb_params.get("speed"),
                "asb_grain": asb_params.get("grain"),
                "asb_style": asb_style,
                "facecam_ratio": asb_params.get("facecam_ratio"),
            }
            if job.clip_metadata and isinstance(job.clip_metadata, list):
                # Preservar metadata original, adicionar pipeline info
                job.clip_metadata = job.clip_metadata + [{"_pipeline": pipeline_meta}]
            db.commit()

    # ── Limpar clips brutos deste job (já foram stitchados) ──
    try:
        import glob as _glob
        clips_dir = "/app/data/clipper/clips"
        pattern = os.path.join(clips_dir, f"job{job_id}_clip*")
        clip_files = _glob.glob(pattern)
        for cf in clip_files:
            os.remove(cf)
        if clip_files:
            logger.info(f"🗑️ Job #{job_id}: {len(clip_files)} clips brutos removidos após stitching")
    except Exception as e:
        logger.warning(f"Job #{job_id}: Falha ao limpar clips brutos: {e}")

    # Inserir na fila de curadoria (PendingApproval)
    MAX_PENDING_APPROVALS = 10  # Limite de vídeos pendentes de aprovação (evita encher disco)
    try:
        # ── Verificar limite de aprovação ──
        with safe_session() as db:
            pending_count = db.query(PendingApproval).filter(
                PendingApproval.status == "pending"
            ).count()
        if pending_count >= MAX_PENDING_APPROVALS:
            logger.warning(f"⛔ Fila de aprovação cheia: {pending_count}/{MAX_PENDING_APPROVALS}. Vídeo do Job #{job_id} descartado.")
            # Limpar o arquivo de vídeo para não ocupar disco
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
                logger.info(f"🗑️ Arquivo descartado: {output_path}")
            return

        file_size = os.path.getsize(output_path) if output_path and os.path.exists(output_path) else 0

        approval_status = "approved" if target_auto_approve else "pending"
        approval_id = None
        with safe_session() as db:
            approval = PendingApproval(
                clip_job_id=job_id,
                video_path=output_path,
                streamer_name=channel_name,
                title=f"{channel_name or 'Clip'} #{job_id}",
                duration_seconds=int(duration),
                file_size_bytes=file_size,
                status=approval_status,
            )
            db.add(approval)
            db.commit()
            db.refresh(approval)
            approval_id = approval.id

        # Pré-gerar caption via Oracle (best-effort, não bloqueia o pipeline)
        try:
            game_name = ""
            clip_blocks = []
            has_content = False
            with safe_session() as db:
                job_for_caption = db.query(ClipJob).filter(ClipJob.id == job_id).first()
                if job_for_caption:
                    metadata_list = job_for_caption.clip_metadata or []
                    transcriptions_list = job_for_caption.whisper_result or []
                    for i, meta in enumerate(metadata_list):
                        if meta.get("game"):
                            game_name = meta["game"]
                        broadcaster = meta.get("broadcaster_name") or meta.get("creator_name") or ""
                        clip_title = meta.get("title") or ""
                        views = meta.get("view_count") or meta.get("views") or 0
                        trans = transcriptions_list[i] if i < len(transcriptions_list) else {}
                        clip_text = (trans.get("text") or "").strip()

                        header = f"CLIP {i + 1}"
                        if broadcaster:
                            header += f" — @{broadcaster}"
                        if clip_title:
                            header += f' | "{clip_title}"'
                        if views:
                            header += f" | {int(views):,} views"
                        block = header + "\n"
                        block += f'Transcrição: "{clip_text}"' if clip_text else "(sem áudio transcrito)"
                        clip_blocks.append(block)
                        if clip_text or clip_title:
                            has_content = True

            if has_content:
                from core.oracle import oracle_client

                streamer = channel_name or "Streamer"
                niche_tag = game_name.lower().replace(' ', '').replace(':', '') if game_name else 'twitch'
                clips_detail = "\n\n".join(clip_blocks) if clip_blocks else "(sem dados de clipes)"

                NON_GAMING = {"just chatting", "irl", "talk shows & podcasts", "asmr", "music", "art",
                              "beauty & body art", "food & drink", "sports", "travel & outdoors",
                              "fitness & health", "pools, hot tubs, and beaches", "politics"}
                is_gaming = game_name.lower().strip() not in NON_GAMING and bool(game_name)
                niche_guidance = (
                    f"games/gameplay → gírias gamer; tom enérgico; use #{niche_tag}" if is_gaming
                    else f"Just Chatting/IRL → drama/humor humano; NUNCA jargão gamer; use #{niche_tag or 'twitch'}"
                )

                system_prompt = f"""Você é copywriter de TikTok especialista em clips de Twitch BR.
Missão: criar UMA frase-gancho de até 150 chars que faz a pessoa PARAR o scroll.

REGRAS DE OURO:
- OBRIGATÓRIO: destaque a emoção principal com CAIXA ALTA no gancho (ex: "PERDEU o controle")
- Use falas reais da transcrição — não invente nada
- Adapte ao nicho: {niche_guidance}
- Mencione {streamer} pelo nome de forma natural
- PT-BR coloquial, gírias atuais, 0-2 emoji
- PROIBIDO: "Neste vídeo...", "Veja só...", prefixos explicativos, aspas ao redor da caption

Responda APENAS em JSON: {{"caption": "...", "hashtags": ["#tag1", "#tag2"]}}
Hashtags: 3-5 tags — mix de alcance (#fyp) + nicho específico (#{niche_tag})"""

                prompt = f"""[CONTEXTO]
Streamer: {streamer} | Categoria: {game_name or "N/A"} | {len(clip_blocks)} clipe(s)

[CLIPES — TRANSCRIÇÕES SEPARADAS]
{clips_detail}

Identifique o MOMENTO-CHAVE (fala mais forte, reação mais intensa) e construa a caption ao redor dele.
Responda SOMENTE com o JSON."""

                full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"
                result = oracle_client.generate_content(
                    prompt_input=full_prompt,
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                )

                import json, re
                content = result.text if hasattr(result, 'text') else str(result)
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    match = re.search(r'\{[^{}]*"caption"[^{}]*\}', content, re.DOTALL)
                    parsed = json.loads(match.group()) if match else {}

                if parsed.get("caption"):
                    with safe_session() as db:
                        appr = db.query(PendingApproval).filter(PendingApproval.id == approval_id).first()
                        if appr:
                            appr.caption = parsed["caption"]
                            appr.hashtags = parsed.get("hashtags", [])[:5]
                            appr.caption_generated = True
                            db.commit()
                    logger.info(f"Job #{job_id}: Caption pré-gerada pelo Oracle ({len(parsed['caption'])} chars)")
            else:
                logger.info(f"Job #{job_id}: Sem transcript, pulando pré-geração de caption.")
        except Exception as caption_err:
            logger.warning(f"Job #{job_id}: Falha na pré-geração de caption (non-blocking): {caption_err}")

        if target_auto_approve:
            logger.info(f"Job #{job_id} Auto-Approved (PendingApproval #{approval_id}).")
            try:
                from core.auto_scheduler import create_queue, schedule_next_batch
                from core.models import Profile, Army
                from core.clipper.uniquifier import generate_variants, InsufficientDiskError
                from core.caption_engine import generate_caption_variations

                with safe_session() as db:
                    # Resolver TODOS os profiles via Army do target (prioridade) ou fallback
                    active_profiles = []
                    target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
                    if target and target.army_id:
                        army = db.query(Army).filter(Army.id == target.army_id).first()
                        if army and army.profiles:
                            active_profiles = [p for p in army.profiles if p.active]

                    if not active_profiles:
                        fallback = db.query(Profile).filter(Profile.active == True).first()
                        if fallback:
                            active_profiles = [fallback]

                    if active_profiles:
                        # Gerar variantes únicas por perfil
                        profile_slugs = [p.slug for p in active_profiles]
                        variants = await generate_variants(
                            source_path=output_path,
                            profile_slugs=profile_slugs,
                        )
                        variant_map = {v["profile_slug"]: v for v in variants}

                        # Recuperar caption gerada (se existir)
                        appr = db.query(PendingApproval).filter(PendingApproval.id == approval_id).first()
                        base_caption = (appr.caption if appr and appr.caption else f"{channel_name or 'Clip'} #{job_id}")
                        base_hashtags = (appr.hashtags if appr and appr.hashtags else [])

                        # Gerar variações de caption
                        caption_vars = await generate_caption_variations(
                            base_caption=base_caption,
                            hashtags=base_hashtags,
                            count=len(active_profiles),
                        )

                        for i, p in enumerate(active_profiles):
                            v = variant_map.get(p.slug, {})
                            p_video_path = v.get("variant_path", output_path) if v.get("success") else output_path
                            p_caption = caption_vars[i]["caption"] if i < len(caption_vars) else base_caption

                            create_queue(
                                profile_slug=p.slug,
                                videos=[{
                                    "path": p_video_path,
                                    "caption": p_caption,
                                    "hashtags": base_hashtags,
                                    "privacy_level": "public_to_everyone",
                                }],
                                posts_per_day=2,
                                schedule_hours=[12, 18],
                                db=db,
                            )
                            result = await schedule_next_batch(
                                profile_slug=p.slug,
                                batch_size=1,
                                db=db,
                            )
                            variant_tag = " [variante]" if v.get("success") and p_video_path != output_path else ""
                            logger.info(f"Job #{job_id} Auto-Enfileirado no perfil @{p.slug}{variant_tag}: {result}")
                        logger.info(f"Job #{job_id} Auto-Enfileirado para {len(active_profiles)} perfil(s): {[p.slug for p in active_profiles]}")
                    else:
                        logger.warning(f"Job #{job_id}: Nenhum profile ativo para auto-enfileirar.")
            except InsufficientDiskError as disk_err:
                logger.warning(
                    f"Job #{job_id}: Disco insuficiente para gerar variantes — "
                    f"mantendo como pendente para aprovação manual. {disk_err}"
                )
            except Exception as sq_err:
                logger.error(f"Erro ao enfileirar Job #{job_id} no Scheduler: {sq_err}", exc_info=True)
        else:
            logger.info(f"Job #{job_id} inserido na fila de curadoria manual (PendingApproval #{approval_id}).")

    except Exception as e:
        logger.error(f"Job #{job_id} concluido mas falhou ao inserir na curadoria: {e}", exc_info=True)


async def process_clip_job(ctx, job_id: int):
    """
    Ponto de entrada do ARQ. Antes de processar o job recebido,
    verifica se ha jobs de alta prioridade que devem ser processados primeiro.
    """
    # Checar se ha job de alta prioridade que deve passar na frente
    actual_job_id = job_id
    try:
        with safe_session() as db:
            priority_job = (
                db.query(ClipJob)
                .filter(ClipJob.status == "pending", ClipJob.priority >= 1)
                .order_by(ClipJob.priority.desc(), ClipJob.id.asc())
                .first()
            )
            if priority_job and priority_job.id != job_id:
                # Ha um job prioritario diferente do que recebemos — processa ele primeiro
                logger.info(f"Job #{priority_job.id} tem prioridade {priority_job.priority}, processando antes de #{job_id}")
                actual_job_id = priority_job.id
                # Resetar prioridade para evitar loop
                priority_job.priority = 0
                db.commit()
    except Exception as e:
        logger.warning(f"Erro ao checar prioridade: {e}")

    try:
        await _process_clip_job_inner(ctx, actual_job_id)
    except Exception as e:
        logger.error(f"Erro fatal orfao processando job #{actual_job_id}: {e}", exc_info=True)
        try:
            _fail_job_db(actual_job_id, str(e), "Falha critica no worker pipeline.")
        except Exception as cleanup_err:
            logger.error(f"Falha secundaria ao marcar job #{actual_job_id} como falhado: {cleanup_err}")

    # Se trocamos o job, re-enfileirar o original para nao perder
    if actual_job_id != job_id:
        try:
            with safe_session() as db:
                orig = db.query(ClipJob).filter(ClipJob.id == job_id, ClipJob.status == "pending").first()
                if orig:
                    from core.config import REDIS_HOST, REDIS_PORT
                    from arq.connections import RedisSettings, create_pool as arq_create_pool
                    pool = await arq_create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
                    try:
                        await pool.enqueue_job("process_clip_job", job_id, _queue_name="clipper:queue")
                        logger.info(f"Job #{job_id} re-enfileirado apos processar prioritario #{actual_job_id}")
                    finally:
                        await pool.close()
        except Exception as e:
            logger.warning(f"Falha ao re-enfileirar job #{job_id}: {e}")

async def startup(ctx):
    """
    Funcao que roda no startup do worker ARQ do Clipper.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logger.info("Clipper Worker Conectado.")

    # Recovery: resetar jobs orfaos que ficaram travados em estados intermediarios
    stuck_statuses = ["processing", "downloading", "transcribing", "editing", "stitching"]
    recovered_ids = []
    with safe_session() as db:
        stuck_jobs = db.query(ClipJob).filter(ClipJob.status.in_(stuck_statuses)).all()
        if stuck_jobs:
            for job in stuck_jobs:
                logger.warning(f"Job #{job.id} orfao (status={job.status}). Resetando para pending.")
                job.status = "pending"
                job.current_step = "Reagendado apos recovery do worker"
                job.progress_pct = 0
                recovered_ids.append(job.id)
            db.commit()
            logger.info(f"{len(stuck_jobs)} jobs orfaos resetados para reprocessamento.")

        # Também buscar jobs pending que nunca foram enfileirados no Redis
        pending_jobs = db.query(ClipJob).filter(ClipJob.status == "pending").all()
        for job in pending_jobs:
            if job.id not in recovered_ids:
                recovered_ids.append(job.id)

    # Re-enfileirar TODOS os pending jobs no Redis (orfaos + já existentes)
    if recovered_ids:
        try:
            from core.config import REDIS_HOST, REDIS_PORT
            from arq.connections import RedisSettings, create_pool as arq_create_pool
            import asyncio
            pool = await arq_create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
            try:
                for job_id in recovered_ids:
                    await pool.enqueue_job("process_clip_job", job_id, _queue_name="clipper:queue")
                    _startup_enqueued_ids.add(job_id)
                    logger.info(f"Job #{job_id} (re)enfileirado no Redis clipper:queue")
            finally:
                await pool.close()
            logger.info(f"✅ {len(recovered_ids)} job(s) pending (re)enfileirados no startup")
        except Exception as e:
            logger.error(f"Falha ao re-enfileirar jobs no startup: {e}", exc_info=True)

    # Iniciar Clipper Scheduler Loop (scan automatico de targets)
    try:
        from core.clipper.scheduler import clipper_scheduler_loop
        import asyncio
        ctx["scheduler_task"] = asyncio.create_task(clipper_scheduler_loop(poll_interval=60))
        logger.info("Clipper Scheduler Loop iniciado (poll=60s).")
    except Exception as e:
        logger.error(f"Falha ao iniciar Clipper Scheduler: {e}", exc_info=True)

    # Iniciar scan periódico de jobs pending órfãos (não enfileirados no Redis)
    try:
        import asyncio
        ctx["orphan_scan_task"] = asyncio.create_task(_orphan_pending_scanner())
        logger.info("Orphan Pending Scanner iniciado (scan a cada 120s).")
    except Exception as e:
        logger.error(f"Falha ao iniciar Orphan Scanner: {e}", exc_info=True)


async def _orphan_pending_scanner():
    """
    Scan periódico que detecta jobs com status 'pending' no DB que não estão
    enfileirados no Redis. Garante que nenhum job fique preso na fila sem
    ser processado.
    """
    import asyncio
    await asyncio.sleep(30)  # Delay inicial para dar tempo ao startup

    while True:
        try:
            with safe_session() as db:
                pending_jobs = db.query(ClipJob).filter(ClipJob.status == "pending").all()
                if pending_jobs:
                    from core.config import REDIS_HOST, REDIS_PORT
                    from arq.connections import RedisSettings, create_pool as arq_create_pool
                    pool = await arq_create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))
                    try:
                        for job in pending_jobs:
                            if job.id in _startup_enqueued_ids:
                                continue
                            await pool.enqueue_job("process_clip_job", job.id, _queue_name="clipper:queue")
                            logger.info(f"[ORPHAN SCAN] Job #{job.id} re-enfileirado (status=pending sem worker)")
                    finally:
                        await pool.close()
        except Exception as e:
            logger.error(f"[ORPHAN SCAN] Erro: {e}")

        # After the first scan, clear the startup set so future scans are not filtered
        _startup_enqueued_ids.clear()
        await asyncio.sleep(120)  # Scan a cada 2 minutos


async def shutdown(ctx):
    # Cancelar scheduler loop se estiver rodando
    scheduler_task = ctx.get("scheduler_task")
    if scheduler_task and not scheduler_task.done():
        scheduler_task.cancel()
        logger.info("Clipper Scheduler Loop cancelado.")
    # Cancelar orphan scanner
    orphan_task = ctx.get("orphan_scan_task")
    if orphan_task and not orphan_task.done():
        orphan_task.cancel()
        logger.info("Orphan Scanner cancelado.")
    logger.info("Clipper Worker Desligando.")




# Config do redis via env
from core.config import REDIS_URL
redis_url = REDIS_URL

class WorkerSettings:
    """Configuracao lida pelo script `arq` na linha de comando."""
    functions = [process_clip_job]
    redis_settings = RedisSettings.from_dsn(redis_url)
    queue_name = "clipper:queue"
    max_jobs = 1  # Conservador devido a VRAM/RAM (Whisper e FFmpeg limitados a 1 por vez neste container)
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 1800  # Pode demorar bastante (download + whisper + edicao + stitch)
