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

    # Buscar channel_name, auto_approve e target_id
    channel_name = None
    target_auto_approve = False
    target_id = None
    with safe_session() as db:
        job_obj = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job_obj and job_obj.target_id:
            target_id = job_obj.target_id
            target = db.query(TwitchTarget).filter(TwitchTarget.id == job_obj.target_id).first()
            if target:
                channel_name = target.channel_name
                target_auto_approve = getattr(target, 'auto_approve', False) or False

    # Filtrar apenas pares clip+transcricao com palavras (B05/B25 fix)
    valid_pairs = []
    for path, trans in zip(local_paths, transcriptions):
        if trans.get("word_count", 0) > 0:
            valid_pairs.append((path, trans))
        else:
            logger.warning(f"Job #{job_id}: Clip {path} sem palavras transcritas, pulando edicao.")

    if not valid_pairs:
        _fail_job_db(job_id, "Nenhum clipe teve palavras transcritas com sucesso.", "Falha: transcricoes vazias.")
        return

    # 3. Gerar ASS & 4. FFmpeg Edit (por clipe individual)
    edited_paths = []

    # Atualiza DB para "editing"
    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "editing"
            job.current_step = f"Editando 0/{len(valid_pairs)} clipes..."
            job.progress_pct = 50
            db.commit()

    for idx, (path, trans) in enumerate(valid_pairs):
        ass_path = None
        try:
            ass_path = generate_ass_for_multiple(
                transcriptions=[trans],
                style_name="opus",
                time_offsets=[0.0]
            )

            edit_res = await edit_clip(
                video_path=path,
                ass_path=ass_path,
                timeout_seconds=900,
                channel_name=channel_name,
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

    # Verify actual duration via ffprobe if result duration seems unreliable (e.g. loop-tail fallback)
    if output_path and os.path.exists(output_path) and duration <= 0:
        try:
            duration = await _get_duration(output_path)
        except Exception:
            pass

    with safe_session() as db:
        job = db.query(ClipJob).filter(ClipJob.id == job_id).first()
        if job:
            job.status = "completed"
            job.current_step = "Concluido!"
            job.progress_pct = 100
            job.output_path = output_path
            job.completed_at = datetime.now(timezone.utc)
            job.duration_seconds = duration
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
            transcript_text = ""
            game_name = ""
            clip_titles = []
            with safe_session() as db:
                job_for_caption = db.query(ClipJob).filter(ClipJob.id == job_id).first()
                if job_for_caption:
                    if job_for_caption.whisper_result:
                        parts = [t.get("text", "") for t in (job_for_caption.whisper_result or []) if t.get("text")]
                        transcript_text = " ".join(parts)
                    if job_for_caption.clip_metadata:
                        for meta in job_for_caption.clip_metadata:
                            if meta.get("game"):
                                game_name = meta["game"]
                            if meta.get("title"):
                                clip_titles.append(meta["title"])

            if transcript_text or clip_titles:
                from core.oracle import oracle_client

                streamer = channel_name or "Streamer"
                context_lines = []
                if game_name:
                    context_lines.append(f"Jogo: {game_name}")
                context_lines.append(f"Streamer: {streamer}")
                if clip_titles:
                    context_lines.append(f"Títulos dos clipes: {' | '.join(clip_titles)}")
                video_context = "\n".join(context_lines)

                system_prompt = f"""Você é a LARI, copywriter de 23 anos que vive de TikTok em São Paulo.
Sua especialidade é criar ganchos que prendem nos primeiros 0.5s de leitura.

ESTILO: Frases curtas e cortantes. Gírias BR atuais. Caps lock estratégico em 1-2 palavras.
Máximo 2-3 linhas. Pode usar 1-2 emoji no máximo.

REGRAS:
- A caption DEVE refletir o conteúdo REAL (use a transcrição e títulos dos clipes)
- NUNCA invente eventos ou falas
- NÃO comece com "Neste vídeo..." ou "Veja só..."
- Responda APENAS em JSON: {{"caption": "...", "hashtags": ["#tag1", "#tag2"]}}
- Gere de 3 a 5 hashtags (MÁXIMO 5): mix de alcance (#fyp #gaming) + nicho (#{game_name.lower().replace(' ', '').replace(':', '') if game_name else 'twitch'})"""

                prompt = f"""[CONTEXTO DO VÍDEO]
{video_context}

[TRANSCRIÇÃO WHISPER]
{transcript_text if transcript_text else "(Sem áudio — baseie-se nos títulos dos clipes)"}"""

                full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"
                result = oracle_client.generate_content(
                    prompt_input=full_prompt,
                    model="llama-3.3-70b-versatile",
                    temperature=0.85,
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

                with safe_session() as db:
                    # Resolver profile via Army do target (prioridade) ou fallback
                    profile = None
                    target = db.query(TwitchTarget).filter(TwitchTarget.id == target_id).first()
                    if target and target.army_id:
                        army = db.query(Army).filter(Army.id == target.army_id).first()
                        if army and army.profiles:
                            for p in army.profiles:
                                if p.active:
                                    profile = p
                                    break

                    if not profile:
                        profile = db.query(Profile).filter(Profile.active == True).first()

                    if profile:
                        create_queue(
                            profile_slug=profile.slug,
                            videos=[{
                                "path": output_path,
                                "caption": f"{channel_name or 'Clip'} #{job_id}",
                                "hashtags": [],
                                "privacy_level": "public_to_everyone",
                            }],
                            posts_per_day=2,
                            schedule_hours=[12, 18],
                            db=db,
                        )
                        result = await schedule_next_batch(
                            profile_slug=profile.slug,
                            batch_size=1,
                            db=db,
                        )
                        logger.info(f"Job #{job_id} Auto-Enfileirado no perfil @{profile.slug}: {result}")
                    else:
                        logger.warning(f"Job #{job_id}: Nenhum profile ativo para auto-enfileirar.")
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
