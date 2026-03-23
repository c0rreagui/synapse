"""
Clipper Vision - Deteccao Biometrica de Facecam via MTCNN (v2)
==============================================================

v2 Melhorias:
- Corner Priority: faces nos cantos da tela (onde ficam facecams) ganham peso extra
- Size Consistency: clusters com tamanho estavel entre frames sao priorizados
- IRL Detection: detecta quando nao ha facecam overlay (streamer na rua, IRL)
  e retorna modo de tracking centralizado no rosto principal

Usa facenet_pytorch.MTCNN para localizar faces humanas reais no video.
MTCNN detecta landmarks faciais biometricos (olhos, nariz, boca), sendo
imune a texturas de personagens de videogame.
"""

import cv2
import logging
import math
from typing import Tuple, Optional, List

logger = logging.getLogger("ClipperVision")

# Frames a serem testados (% da duracao)
SAMPLE_POSITIONS = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]

# Confianca minima para pertinência inicial do MTCNN
MIN_CONFIDENCE = 0.85

# Limiar de area facial para detectar modo IRL (face ocupa >15% da tela)
IRL_FACE_AREA_THRESHOLD = 0.15

# Corner bonus: faces nos 25% de borda da tela ganham peso extra
CORNER_MARGIN = 0.25
CORNER_BONUS = 1.5  # 50% de peso extra

# Size consistency bonus
SIZE_CONSISTENCY_BONUS = 1.3  # 30% de peso extra para tamanho estavel


def _read_frame_at(cap: cv2.VideoCapture, position: float):
    """Le um frame na posicao relativa (0.0 a 1.0) do video."""
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    target = int(total_frames * position)
    target = max(0, min(target, total_frames - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, target)
    ret, frame = cap.read()
    return frame if ret else None


def _detect_all_faces_mtcnn(frame, detector) -> List[Tuple[float, int, int, int, int]]:
    """
    Roda MTCNN no frame e retorna lista de (confianca, x, y, w, h)
    para todas as faces com confianca >= MIN_CONFIDENCE.
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    boxes, probs = detector.detect(rgb_frame)

    valid_faces = []
    if boxes is None or probs is None or len(boxes) == 0:
        return valid_faces

    for box, prob in zip(boxes, probs):
        if prob is not None and prob >= MIN_CONFIDENCE:
            x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            if x2 > x1 and y2 > y1:
                valid_faces.append((float(prob), x1, y1, x2 - x1, y2 - y1))

    return valid_faces


def _compute_iou(boxA, boxB):
    """Calcula a Intersection over Union (IoU) entre dois bounding boxes (x, y, w, h)."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0

    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou


def _is_in_corner(x, y, w, h, frame_w, frame_h) -> bool:
    """Verifica se o centro da face esta em um dos 4 cantos da tela."""
    cx = x + w / 2
    cy = y + h / 2
    margin_x = frame_w * CORNER_MARGIN
    margin_y = frame_h * CORNER_MARGIN

    in_left = cx < margin_x
    in_right = cx > (frame_w - margin_x)
    in_top = cy < margin_y
    in_bottom = cy > (frame_h - margin_y)

    return (in_left or in_right) and (in_top or in_bottom)


def _size_std_dev(cluster) -> float:
    """Calcula o desvio padrao relativo do tamanho das faces no cluster."""
    if len(cluster) < 2:
        return 0.0
    areas = [f[3] * f[4] for f in cluster]  # w * h
    mean = sum(areas) / len(areas)
    if mean == 0:
        return 0.0
    variance = sum((a - mean) ** 2 for a in areas) / len(areas)
    return math.sqrt(variance) / mean  # Coeficiente de variacao (0 = perfeito)


def _cluster_score(cluster, frame_w, frame_h) -> float:
    """
    Calcula score do cluster combinando:
    1. Frequencia (quantos frames aparece) — base
    2. Corner priority (facecams ficam nos cantos) — bonus 50%
    3. Size consistency (tamanho estavel = facecam, instavel = conteudo) — bonus 30%
    """
    freq = len(cluster)
    conf_sum = sum(f[0] for f in cluster)

    # Base score: frequencia + confianca
    score = freq + (conf_sum * 0.1)

    # Corner bonus: se a maioria das deteccoes esta em um canto
    corner_count = sum(
        1 for f in cluster
        if _is_in_corner(f[1], f[2], f[3], f[4], frame_w, frame_h)
    )
    corner_ratio = corner_count / freq if freq > 0 else 0
    if corner_ratio >= 0.5:  # Pelo menos metade das deteccoes em canto
        score *= CORNER_BONUS
        logger.debug(f"  Cluster corner bonus: {corner_ratio:.0%} deteccoes em canto")

    # Size consistency bonus: menor variacao = mais provavel ser facecam
    size_cv = _size_std_dev(cluster)
    if size_cv < 0.3:  # Variacao < 30% = muito estavel
        score *= SIZE_CONSISTENCY_BONUS
        logger.debug(f"  Cluster size bonus: CV={size_cv:.2f} (estavel)")

    return score


# ── Singleton MTCNN ──────────────────────────────────────────────────────
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
                thresholds=[0.7, 0.8, 0.9],
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
    Detecta a facecam do streamer no video usando MTCNN + scoring inteligente.

    Melhorias v2:
    - Corner Priority: faces nos cantos (onde ficam facecams) ganham peso
    - Size Consistency: facecams tem tamanho estavel vs faces em conteudo de react
    - IRL Detection: se a maior face ocupa >15% da tela, assume IRL mode

    Retorna (x, y, w, h) para crop, ou None se nenhuma face consistente encontrada.
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
        total_area = frame_width * frame_height

        # Filtro geometrico: face >= 0.5% da tela (filtra avatares de jogo)
        min_face_area = total_area * 0.005

        all_detections = []
        frames_tested = 0

        for pos in SAMPLE_POSITIONS:
            frame = _read_frame_at(cap, pos)
            if frame is None:
                continue

            frames_tested += 1
            faces = _detect_all_faces_mtcnn(frame, detector)

            for f in faces:
                _, bx, by, bw, bh = f
                face_area = bw * bh
                if face_area >= min_face_area:
                    all_detections.append(f)

        cap.release()

        if not all_detections:
            logger.warning(f"Nenhuma face detectada em {frames_tested} frames.")
            return None

        logger.info(f"{len(all_detections)} faces detectadas em {frames_tested} frames.")

        # ── IRL Detection ──
        # Se a maior face ocupa >15% da tela, provavelmente é IRL (sem facecam overlay)
        max_face_area_ratio = max(
            (f[3] * f[4]) / total_area for f in all_detections
        )
        is_irl = max_face_area_ratio > IRL_FACE_AREA_THRESHOLD

        if is_irl:
            logger.info(
                f"🎥 IRL MODE detectado (face ocupa {max_face_area_ratio:.1%} da tela). "
                f"Priorizando face mais frequente (streamer)."
            )

        # ── Clusterizacao Geo-Temporal (IoU) ──
        clusters = []

        for det in all_detections:
            added = False
            det_box = det[1:]

            for cluster in clusters:
                ref_box = cluster[0][1:]
                iou = _compute_iou(det_box, ref_box)
                if iou >= 0.30:
                    cluster.append(det)
                    added = True
                    break

            if not added:
                clusters.append([det])

        logger.info(f"{len(clusters)} clusters espaciais formados.")

        # ── Eleicao por Score Combinado ──
        best_cluster = max(
            clusters,
            key=lambda c: _cluster_score(c, frame_width, frame_height)
        )

        best_score = _cluster_score(best_cluster, frame_width, frame_height)
        logger.info(
            f"Cluster vencedor: {len(best_cluster)} deteccoes, score={best_score:.2f}"
        )

        # Melhor deteccao dentro do cluster (maior confianca biometrica)
        best_detection = max(best_cluster, key=lambda f: f[0])
        _, bx, by, bw, bh = best_detection

        # ── IRL: padding maior para contexto ──
        if is_irl:
            # Em IRL, queremos mais contexto ao redor do rosto
            padding_pct_up = 1.50
            padding_pct_down = 1.00
            padding_pct_sides = 2.00
            logger.info("IRL: padding expandido para mais contexto (corpo/cenario)")

        # Calcular padding
        pad_up = int(bh * padding_pct_up)
        pad_down = int(bh * padding_pct_down)
        pad_sides = int(bw * padding_pct_sides)

        # Aplicar padding com bounds check
        x1 = max(0, bx - pad_sides)
        y1 = max(0, by - pad_up)
        x2 = min(frame_width, bx + bw + pad_sides)
        y2 = min(frame_height, by + bh + pad_down)

        box = (x1, y1, x2 - x1, y2 - y1)

        mode_str = "IRL" if is_irl else "FACECAM"
        logger.info(f"[{mode_str}] Box final: {box} (pad: up={pad_up} down={pad_down} sides={pad_sides})")

        return box

    except Exception as e:
        logger.error(f"Falha critica no motor Vision MTCNN: {e}")
        return None
