"""
Vision Faculty - Visual Analysis
The eyes of the Oracle. Extracts and analyzes visual content from videos and images.
Migrated from: visual_cortex.py
Enhanced: 2026-02-04 - Unified flows, cache, intelligent multi-frame
"""
import logging
import os
import subprocess
import hashlib
import base64
import io
import time
from typing import List, Dict, Any, Union, Optional
import PIL.Image

logger = logging.getLogger(__name__)

# In-memory cache for visual analysis (hash -> result)
_VISION_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = 3600  # 1 hour


class VisionFaculty:
    """
    The Vision: Visual Analysis Engine.
    Extracts key frames from video and performs multimodal analysis.
    
    Features:
    - Unified analysis for video paths OR base64 frames
    - Intelligent scene detection to reduce API calls
    - Visual cache to avoid re-processing
    - Avatar/thumbnail specific analysis
    """

    def __init__(self, client):
        self.client = client
        self.temp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "processing")
        self.vision_model = "meta-llama/llama-4-maverick-17b-128e-instruct"

    # ========== CACHE MANAGEMENT ==========
    
    def _get_cache_key(self, content: Union[str, List[str]]) -> str:
        """Generate cache key from video path or frame list."""
        if isinstance(content, str) and os.path.exists(content):
            # Video file: use file hash
            with open(content, 'rb') as f:
                return hashlib.md5(f.read(1024*1024)).hexdigest()  # First 1MB
        elif isinstance(content, list):
            # Base64 frames: hash concatenated content
            concat = "".join([f[:100] for f in content])  # First 100 chars of each
            return hashlib.md5(concat.encode()).hexdigest()
        return hashlib.md5(str(content).encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve from cache if not expired."""
        if key in _VISION_CACHE:
            entry = _VISION_CACHE[key]
            if time.time() - entry.get("_cached_at", 0) < _CACHE_TTL:
                logger.info(f"[VISION] Cache HIT for {key[:8]}...")
                return entry
            else:
                del _VISION_CACHE[key]
        return None
    
    def _set_cache(self, key: str, result: Dict[str, Any]):
        """Store result in cache."""
        result["_cached_at"] = time.time()
        _VISION_CACHE[key] = result
        logger.info(f"[VISION] Cached result for {key[:8]}...")

    # ========== FRAME EXTRACTION ==========

    def extract_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """Uses FFmpeg to extract N evenly spaced frames from a video."""
        if not os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return []

        frames_dir = os.path.join(self.temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        # Clean old frames
        for f in os.listdir(frames_dir):
            if f.startswith("frame_"):
                try:
                    os.remove(os.path.join(frames_dir, f))
                except:
                    pass

        output_pattern = os.path.join(frames_dir, "frame_%03d.jpg")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", "fps=0.5",
            "-vframes", str(num_frames),
            output_pattern
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            frames = sorted([
                os.path.join(frames_dir, f)
                for f in os.listdir(frames_dir)
                if f.startswith("frame_") and f.endswith(".jpg")
            ])
            return frames[:num_frames]
        except Exception as e:
            logger.error(f"FFmpeg failed: {e}")
            return []

    # ========== INTELLIGENT SCENE DETECTION ==========
    
    def select_representative_frames(self, frames_b64: List[str], max_frames: int = 5) -> List[str]:
        """
        Intelligently select representative frames from a larger set.
        Uses simple heuristic: first, middle, last + 2 distributed.
        """
        if len(frames_b64) <= max_frames:
            return frames_b64
        
        total = len(frames_b64)
        indices = [
            0,                          # First frame (hook)
            total // 4,                 # 25% mark
            total // 2,                 # Middle
            (total * 3) // 4,           # 75% mark
            total - 1                   # Last frame
        ]
        
        # Remove duplicates and sort
        indices = sorted(set(indices))[:max_frames]
        
        selected = [frames_b64[i] for i in indices if i < total]
        logger.info(f"[VISION] Selected {len(selected)} representative frames from {total}")
        return selected

    # ========== UNIFIED ANALYSIS ==========

    async def analyze_unified(
        self, 
        source: Union[str, List[str]], 
        prompt_override: str = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Unified analysis method that handles:
        - Video file paths (extracts frames via ffmpeg)
        - List of base64 image strings (from frontend)
        
        Args:
            source: Video path OR list of base64 frame strings
            prompt_override: Custom prompt for analysis
            use_cache: Whether to use visual cache
        
        Returns:
            Dict with visual_description, frames_analyzed, etc.
        """
        if not self.client:
            return {"error": "Oracle Vision is offline", "visual_description": ""}
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(source)
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        # Prepare frames
        image_parts = []
        
        if isinstance(source, str) and os.path.exists(source):
            # Video file path
            logger.info(f"[VISION] Analyzing video file: {source}")
            frame_paths = self.extract_frames(source, num_frames=5)
            for fp in frame_paths:
                try:
                    img = PIL.Image.open(fp)
                    image_parts.append(img)
                except Exception as e:
                    logger.warning(f"Failed to load frame {fp}: {e}")
                    
        elif isinstance(source, list):
            # Base64 frames from frontend
            logger.info(f"[VISION] Analyzing {len(source)} base64 frames")
            
            # Apply intelligent selection
            selected_frames = self.select_representative_frames(source, max_frames=5)
            
            for frame_b64 in selected_frames:
                try:
                    # Clean base64 header if present
                    if "," in frame_b64:
                        frame_b64 = frame_b64.split(",")[1]
                    
                    img_data = base64.b64decode(frame_b64)
                    img = PIL.Image.open(io.BytesIO(img_data))
                    image_parts.append(img)
                except Exception as e:
                    logger.warning(f"Failed to decode base64 frame: {e}")
        else:
            return {"error": "Invalid source type", "visual_description": ""}
        
        if not image_parts:
            return {"error": "No frames to analyze", "visual_description": ""}
        
        # Build prompt
        default_prompt = """
        Analise estes frames de um video TikTok.
        Descreva em 2-3 frases curtas:
        1. QUEM: Quantas pessoas, aparencia geral
        2. O QUE: Acao principal acontecendo
        3. ONDE: Ambiente/cenario
        
        Seja objetivo e descritivo. Responda em portugues.
        """
        
        vision_prompt = [
            prompt_override or default_prompt,
            *image_parts
        ]
        
        try:
            response = self.client.generate_content(
                vision_prompt, 
                model=self.vision_model
            )
            
            result = {
                "visual_description": response.text.strip(),
                "frames_analyzed": len(image_parts),
                "source_type": "video_file" if isinstance(source, str) else "base64_frames",
                "faculty": "vision"
            }
            
            # Cache result
            if use_cache:
                self._set_cache(cache_key, result)
            
            logger.info(f"[VISION] Analysis complete: {result['visual_description'][:80]}...")
            return result
            
        except Exception as e:
            if "429" in str(e):
                logger.warning("[VISION] Rate limited (429)")
                return {
                    "visual_description": "",
                    "frames_analyzed": len(image_parts),
                    "status": "rate_limited",
                    "error": "Rate limited"
                }
            logger.error(f"[VISION] Analysis failed: {e}")
            return {"error": str(e), "visual_description": ""}

    # ========== LEGACY METHODS (for backward compatibility) ==========

    async def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """Legacy method - redirects to unified analysis."""
        result = await self.analyze_unified(video_path)
        # Map to legacy format
        return {
            "visual_analysis": result.get("visual_description", ""),
            "frames_analyzed": result.get("frames_analyzed", 0),
            "faculty": "vision"
        }

    async def analyze_thumbnail(self, image_path: str) -> Dict[str, Any]:
        """Analyzes a single image (thumbnail, avatar, etc.)"""
        if not self.client or not os.path.exists(image_path):
            return {"error": "Cannot analyze image", "score": 0}

        try:
            img = PIL.Image.open(image_path)
            prompt = [
                """Analise esta foto de perfil/avatar do TikTok.
                De uma nota de 1 a 10 para apelo visual.
                Responda em JSON:
                {"score": X, "reason": "motivo curto", "improvement": "sugestao"}
                """,
                img
            ]
            response = self.client.generate_content(prompt, model=self.vision_model)
            
            # Try to parse JSON
            import json
            text = response.text.strip()
            try:
                # Find JSON in response
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end > start:
                    data = json.loads(text[start:end])
                    return {
                        "score": data.get("score", 5),
                        "reason": data.get("reason", ""),
                        "improvement": data.get("improvement", ""),
                        "faculty": "vision"
                    }
            except:
                pass
            
            return {"analysis": text, "faculty": "vision"}
        except Exception as e:
            return {"error": str(e), "score": 0}

    # ========== AVATAR ANALYSIS FOR SEO AUDIT ==========
    
    async def analyze_avatar_for_audit(self, image_path: str) -> Dict[str, Any]:
        """
        Specialized avatar analysis for SEO Audit.
        Returns structured feedback for profile optimization.
        """
        if not self.client or not os.path.exists(image_path):
            return {
                "avatar_score": 0,
                "avatar_feedback": "Imagem nao disponivel",
                "avatar_suggestions": []
            }
        
        try:
            img = PIL.Image.open(image_path)
            prompt = [
                """Voce e um especialista em branding de TikTok.
                Analise esta foto de perfil e de feedback estruturado.
                
                Responda APENAS em JSON:
                {
                    "score": 1-10,
                    "is_face_visible": true/false,
                    "is_high_quality": true/false,
                    "brand_consistency": "forte/media/fraca",
                    "suggestions": ["sugestao 1", "sugestao 2"]
                }
                """,
                img
            ]
            
            response = self.client.generate_content(prompt, model=self.vision_model)
            
            import json
            text = response.text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            
            if start != -1 and end > start:
                data = json.loads(text[start:end])
                return {
                    "avatar_score": data.get("score", 5),
                    "avatar_face_visible": data.get("is_face_visible", False),
                    "avatar_quality": data.get("is_high_quality", False),
                    "avatar_brand": data.get("brand_consistency", "media"),
                    "avatar_suggestions": data.get("suggestions", []),
                    "faculty": "vision"
                }
            
            return {"avatar_score": 5, "avatar_feedback": text, "avatar_suggestions": []}
            
        except Exception as e:
            logger.error(f"[VISION] Avatar analysis failed: {e}")
            return {
                "avatar_score": 0,
                "avatar_feedback": f"Erro: {e}",
                "avatar_suggestions": []
            }

    async def analyze_profile_aesthetics(self, screenshot_path: str) -> Dict[str, Any]:
        """
        Analyzes the full profile screenshot for aesthetic quality and branding.
        """
        if not self.client or not os.path.exists(screenshot_path):
            return {
                "aesthetics_score": 0,
                "visual_style": "N/A",
                "layout_analysis": "Screenshot skipped"
            }

        try:
            img = PIL.Image.open(screenshot_path)
            # Resize if too large to save tokens/latency, but keep readable
            img.thumbnail((1280, 1280)) 
            
            prompt = [
                """Voce e um Diretor de Arte e Especialista em Branding Digital.
                Analise este screenshot de um perfil do TikTok.
                
                Avalie:
                1. Coesao Visual (Core, Estilo)
                2. Clareza do layout
                3. Profissionalismo
                
                Responda APENAS em JSON:
                {
                    "aesthetics_score": 1-10,
                    "visual_style": "Ex: Minimalista, Caotico, Dark, Vibrante",
                    "color_palette": ["cor1", "cor2"],
                    "branding_consistency": "Alta/Media/Baixa",
                    "critique": "Breve analise critica (1 frase)",
                    "tips": ["Dica visual 1", "Dica visual 2"]
                }
                """,
                img
            ]
            
            response = self.client.generate_content(prompt, model=self.vision_model)
            
            import json
            text = response.text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            
            if start != -1 and end > start:
                data = json.loads(text[start:end])
                data["faculty"] = "vision"
                return data
                
            return {
                "aesthetics_score": 5, 
                "visual_style": "Unknown", 
                "critique": text,
                "faculty": "vision"
            }
            
        except Exception as e:
            logger.error(f"[VISION] Aesthetics analysis failed: {e}")
            return {
                "aesthetics_score": 0,
                "error": str(e)
            }

