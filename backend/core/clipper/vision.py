"""
Clipper Vision - Deteccao Biometrica de Facecam via MTCNN
=========================================================

Usa facenet_pytorch.MTCNN para localizar faces humanas reais no video.
MTCNN detecta landmarks faciais biometricos (olhos, nariz, boca), sendo
imune a texturas de personagens de videogame (ex: GTA V).

Testa 10 frames distribuídos e aplica Clusterização Geo-Temporal usando IoU.
Faces voláteis (emotes, alertas) não ganham frequência de quadros e
são purgadas matematicamente. O cluster mais presente na tela elege o Mestre.

Retorna coordenadas (x, y, w, h) prontas para FFmpeg crop, ou None
se nenhuma face real consistente for encontrada.
"""

import cv2
import logging
from typing import Tuple, Optional, List

logger = logging.getLogger("ClipperVision")

# Frames a serem testados (% da duracao)
SAMPLE_POSITIONS = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]

# Confianca minima para pertinência inicial do MTCNN
MIN_CONFIDENCE = 0.85


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
    # MTCNN espera RGB; OpenCV carrega BGR
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detectar faces com probabilidades
    boxes, probs = detector.detect(rgb_frame)

    valid_faces = []
    if boxes is None or probs is None or len(boxes) == 0:
        return valid_faces

    for box, prob in zip(boxes, probs):
        if prob is not None and prob >= MIN_CONFIDENCE:
            x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            # Validação geométrica básica
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
    Testa 10 frames com MTCNN, aplica Clusterização Geo-Temporal (IoU) e
    retorna a bounding box (x, y, w, h) do cluster eleito da facecam autêntica.

    Usa padding proporcional estrito. 
    Retorna None se nenhuma face real e consistente for encontrada.
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
        
        # Filtro de chão geométrico: rosto (sem o padding) deve ocupar >= 0.5% da tela.
        # Em streams de gameplay (ex: Rocket League, GTA), a facecam ocupa um canto pequeno
        # da tela 1920x1080, resultando em faces de ~120x150px (~0.87% da área).
        # O piso de 0.5% filtra avatares de jogo (~22x29px, ~600px²) sem rejeitar facecams reais.
        min_face_area = total_area * 0.005

        all_detections = []  # Lista de (conf, x, y, w, h)
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
                    logger.info(
                        f"Face detectada no frame {pos:.0%}: "
                        f"x={bx}, y={by}, dim={bw}x{bh}, conf={f[0]:.3f}"
                    )

        cap.release()

        if not all_detections:
            logger.warning(f"Nenhuma face real/valida detectada geometricamente em {frames_tested} frames lidos.")
            return None

        # Clusterização Geo-Temporal baseada em Overlap de Coordenadas (IoU)
        clusters = []  # Lista de listas contendo rostos: [ [face1, face2], [face3] ]
        
        for det in all_detections:
            added = False
            det_box = det[1:]  # Passando apenas (x, y, w, h)
            
            for cluster in clusters:
                # Usa o arquétipo do primeiro rosto do cluster como Âncora referencial
                ref_box = cluster[0][1:]
                iou = _compute_iou(det_box, ref_box)
                
                # Tolerância branda de 30% de engajamento (absorve recline na cadeira/zoom do streamer)
                if iou >= 0.30:
                    cluster.append(det)
                    added = True
                    break
                    
            if not added:
                # O rosto mora em uma area da tela nova, iniciamos um sub-grupo novo
                clusters.append([det])

        logger.info(f"Rostos consolidados em {len(clusters)} clusters espaciais.")

        # Eleição por Frequência Absoluta
        # Se empatar em votos (len), usa a soma das confianças como desempate matemático
        best_cluster = max(clusters, key=lambda c: (len(c), sum(f[0] for f in c)))
        
        logger.info(f"Cluster vencedor eleito com {len(best_cluster)} quadros consistentes e presentes.")

        # Dentro do cluster vencedor, pega cirurgicamente a captura com maior nota biométrica 
        # para usar como centro perfeito de ancoragem visual
        best_detection = max(best_cluster, key=lambda f: f[0])
        _, bx, by, bw, bh = best_detection

        # Calcular padding em pixels relativo ao tamanho absoluto do rosto eleito
        pad_up = int(bh * padding_pct_up)
        pad_down = int(bh * padding_pct_down)
        pad_sides = int(bw * padding_pct_sides)

        # Aplicar padding geométrico assegurando não desabar para fora da resolução nativa global
        x1 = max(0, bx - pad_sides)
        y1 = max(0, by - pad_up)
        x2 = min(frame_width, bx + bw + pad_sides)
        y2 = min(frame_height, by + bh + pad_down)

        box = (x1, y1, x2 - x1, y2 - y1)
        logger.info(f"Facecam Box computada (Tight): pad_up={pad_up}, pad_down={pad_down}, pad_sides={pad_sides}")
        logger.info(f"Facecam Box final enquadrada (Cluster IoU): {box}")
        
        return box

    except Exception as e:
        logger.error(f"Falha critica no motor Vision MTCNN: {e}")
        return None
