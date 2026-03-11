"""
Clipper Vision - Deteccao Biometrica de Facecam via MTCNN
=========================================================

Usa facenet_pytorch.MTCNN para localizar faces humanas reais no video.
MTCNN detecta landmarks faciais biometricos (olhos, nariz, boca), sendo
imune a texturas de personagens de videogame (ex: GTA V).

Testa 5 frames distintos (10%, 30%, 50%, 70%, 90%) e retorna a
bounding box com maior confianca, expandida com padding geometrico
para englobar o cenario da webcam (nao apenas o rosto).

Retorna coordenadas (x, y, w, h) prontas para FFmpeg crop, ou None
se nenhuma face real for encontrada (editor aplica fallback generico).
"""

import cv2
import logging
from typing import Tuple, Optional

logger = logging.getLogger("ClipperVision")

# Frames a serem testados (% da duracao)
SAMPLE_POSITIONS = [0.10, 0.30, 0.50, 0.70, 0.90]

# Confianca minima para MTCNN (alto threshold = face real confirmada)
MIN_CONFIDENCE = 0.90


def _read_frame_at(cap: cv2.VideoCapture, position: float):
    """Le um frame na posicao relativa (0.0 a 1.0) do video."""
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    target = int(total_frames * position)
    target = max(0, min(target, total_frames - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, target)
    ret, frame = cap.read()
    return frame if ret else None


def _detect_face_mtcnn(frame, detector) -> Optional[Tuple[float, int, int, int, int]]:
    """
    Roda MTCNN no frame e retorna (confianca, x, y, w, h) da melhor
    face biometrica detectada.
    Retorna None se nenhuma face real encontrada.
    """
    # MTCNN espera RGB; OpenCV carrega BGR
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detectar faces com probabilidades
    boxes, probs = detector.detect(rgb_frame)

    if boxes is None or probs is None or len(boxes) == 0:
        return None

    # Filtrar por confianca minima e pegar a melhor
    best_conf = -1.0
    best_box = None

    for box, prob in zip(boxes, probs):
        if prob is not None and prob >= MIN_CONFIDENCE and prob > best_conf:
            best_conf = float(prob)
            best_box = box

    if best_box is None:
        return None

    x1, y1, x2, y2 = int(best_box[0]), int(best_box[1]), int(best_box[2]), int(best_box[3])
    return (best_conf, x1, y1, x2 - x1, y2 - y1)

# ── Singleton MTCNN ──────────────────────────────────────────────────────
# Modelo carregado UMA vez e reutilizado entre chamadas (salva ~2-3s por clipe)
_MTCNN_INSTANCE = None

def _get_detector():
    """Retorna a instancia singleton do MTCNN, criando na primeira chamada."""
    global _MTCNN_INSTANCE
    if _MTCNN_INSTANCE is None:
        try:
            from facenet_pytorch import MTCNN
            import torch
            device = torch.device("cpu")
            _MTCNN_INSTANCE = MTCNN(
                keep_all=True,
                device=device,
                thresholds=[0.7, 0.8, 0.9],  # P-Net, R-Net, O-Net
                min_face_size=40,
            )
            logger.info("MTCNN singleton inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao inicializar MTCNN: {e}")
            return None
    return _MTCNN_INSTANCE


def detect_facecam_box(
    video_path: str,
    padding_pct_up: float = 1.00,
    padding_pct_down: float = 0.50,
    padding_pct_sides: float = 1.50,
    **kwargs,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Testa 5 frames com MTCNN e retorna a bounding box (x, y, w, h)
    da face real detectada.

    Usa padding proporcional estrito. Margens altamente conservadoras para
    isolar rosto e cadeira de streamer, sem vazar para a gameplay nativa
    abaixo da borda natural da webcam (pad_down = 0).

    Retorna None se nenhuma face real for encontrada.
    """
    try:
        detector = _get_detector()
        if detector is None:
            logger.error("MTCNN nao disponivel. Pulando deteccao facial.")
            return None

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Nao foi possivel abrir o video: {video_path}")
            return None

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        best_detection = None  # (conf, x, y, w, h)

        for pos in SAMPLE_POSITIONS:
            frame = _read_frame_at(cap, pos)
            if frame is None:
                logger.warning(f"Falha ao ler frame na posicao {pos:.0%}.")
                continue

            det = _detect_face_mtcnn(frame, detector)
            if det:
                conf, fx, fy, fw, fh = det
                logger.info(
                    f"Face detectada no frame {pos:.0%}: "
                    f"x={fx}, y={fy}, dim={fw}x{fh}, conf={conf:.3f}"
                )
                if best_detection is None or conf > best_detection[0]:
                    best_detection = det

        cap.release()

        if best_detection is None:
            logger.warning(
                f"Nenhuma face real detectada em {len(SAMPLE_POSITIONS)} frames."
            )
            return None

        _, bx, by, bw, bh = best_detection

        # Calcular padding em pixels relativo ao tamanho do rosto detectado
        pad_up = int(bh * padding_pct_up)
        pad_down = int(bh * padding_pct_down)
        pad_sides = int(bw * padding_pct_sides)

        # Aplicar padding geometrico seguro
        x1 = max(0, bx - pad_sides)
        y1 = max(0, by - pad_up)
        x2 = min(frame_width, bx + bw + pad_sides)
        y2 = min(frame_height, by + bh + pad_down)

        box = (x1, y1, x2 - x1, y2 - y1)
        logger.info(f"Facecam Box computada (Tight): pad_up={pad_up}, pad_down={pad_down}, pad_sides={pad_sides}")
        logger.info(f"Facecam Box final (MTCNN): {box}")
        return box

    except Exception as e:
        logger.error(f"Falha no submodulo Vision: {e}")
        return None

