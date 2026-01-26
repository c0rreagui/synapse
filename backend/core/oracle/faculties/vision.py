"""
Vision Faculty - Visual Analysis
The eyes of the Oracle. Extracts and analyzes visual content from videos and images.
Migrated from: visual_cortex.py
"""
import logging
import os
import subprocess
from typing import List, Dict, Any
import PIL.Image

logger = logging.getLogger(__name__)


class VisionFaculty:
    """
    The Vision: Visual Analysis Engine.
    Extracts key frames from video and performs multimodal analysis.
    """

    def __init__(self, client):
        self.client = client
        self.temp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "processing")

    def extract_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """
        Uses FFmpeg to extract N evenly spaced frames from a video.
        """
        if not os.path.exists(video_path):
            logger.error(f"❌ Video not found: {video_path}")
            return []

        frames_dir = os.path.join(self.temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

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
            logger.error(f"[ERROR] FFmpeg failed: {e}")
            return []

    async def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Extracts frames and asks LLM to analyze the visual hook.
        """
        if not self.client:
            return {"error": "Oracle Vision is offline"}

        logger.info(f"[VISION] Oracle.Vision: Processing {video_path}")

        frames = self.extract_frames(video_path)
        if not frames:
            return {"error": "No frames extracted"}

        image_parts = []
        for f in frames:
            try:
                img = PIL.Image.open(f)
                image_parts.append(img)
            except Exception as e:
                logger.error(f"Failed to load image {f}: {e}")

        prompt = [
            "Analyze these frames from a TikTok video.",
            "Identify the visual hook (first frame), pacing, and key visual elements.",
            "Explain WHY this is visually engaging in one sentence.",
            *image_parts
        ]

        try:
            response = self.client.generate_content(prompt)
            return {
                "visual_analysis": response.text.strip(),
                "frames_analyzed": len(frames),
                "faculty": "vision"
            }
        except Exception as e:
            if "429" in str(e):
                logger.warning("[WARNING] Oracle.Vision Rate Limited (429)")
                return {
                    "visual_analysis": "Rate limited. Try again later.",
                    "frames_analyzed": len(frames),
                    "status": "rate_limited"
                }
            logger.error(f"[ERROR] Vision Analysis Failed: {e}")
            return {"error": str(e)}

    async def analyze_thumbnail(self, image_path: str) -> Dict[str, Any]:
        """
        Analyzes a single image (thumbnail, avatar, etc.)
        """
        if not self.client or not os.path.exists(image_path):
            return {"error": "Cannot analyze image"}

        try:
            img = PIL.Image.open(image_path)
            prompt = [
                "Analyze this TikTok thumbnail/avatar.",
                "Score it 1-10 for visual appeal and explain why.",
                img
            ]
            response = self.client.generate_content(prompt)
            return {"analysis": response.text.strip(), "faculty": "vision"}
        except Exception as e:
            return {"error": str(e)}
