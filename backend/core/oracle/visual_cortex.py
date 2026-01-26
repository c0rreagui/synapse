import logging
import os
import subprocess
from typing import List, Dict, Any
from core.oracle.client import oracle_client
import PIL.Image

logger = logging.getLogger(__name__)

class VisualCortex:
    """
    The Visual Cortex: Eyes of the Oracle.
    Extracts key frames from video and performs multimodal analysis using Groq Vision.
    """

    def __init__(self):
        self.client = oracle_client
        self.temp_dir = "/app/processing" # Shared volume

    def extract_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """
        Uses FFmpeg to extract N evenly spaced frames from a video.
        """
        if not os.path.exists(video_path):
            logger.error(f"❌ Video not found: {video_path}")
            return []

        # Ensure output dir exists
        frames_dir = os.path.join(self.temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        # We use a simple strategy: extract 1 frame every X seconds isn't enough because we want exactly N frames.
        # So we use the 'select' filter with expressions? Or just simple fps filter?
        # Simpler: Extract 5 screenshots at approximate intervals.
        # Actually, let's just extract 1 fps for now and take the first 5?
        # Better: use 'vf fps=1/duration*N' logic? Too complex.
        
        output_pattern = os.path.join(frames_dir, "frame_%03d.jpg")
        
        # Command to extract 1 frame every second (simple start)
        # ffmpeg -i input.mp4 -vf fps=1 out%d.jpg
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", "fps=0.5", # 1 frame every 2 seconds
            "-vframes", str(num_frames), # Stop after N frames
            output_pattern
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Gather generated files
            frames = sorted([
                os.path.join(frames_dir, f) 
                for f in os.listdir(frames_dir) 
                if f.startswith("frame_") and f.endswith(".jpg")
            ])
            return frames[:num_frames]
        except Exception as e:
            logger.error(f"❌ FFmpeg failed: {e}")
            return []

    async def analyze_video_content(self, video_path: str) -> Dict[str, Any]:
        """
        Extracts frames and asks Oracle Vision (Groq) to analyze the visual hook.
        """
        if not self.client:
            return {"error": "Visual Cortex Offline"}

        logger.info(f"VisualCortex: Processing {video_path}")

        # 1. Extract Frames
        frames = self.extract_frames(video_path)
        if not frames:
            return {"error": "No frames extracted"}

        # 2. Load Images for Vision Engine
        # Oracle Client wrapper accepts PIL Images directly
        image_parts = []
        for f in frames:
            try:
                img = PIL.Image.open(f)
                image_parts.append(img)
            except Exception as e:
                logger.error(f"Failed to load image {f}: {e}")

        # 3. Construct Multimodal Prompt
        prompt = [
            "Analyze these frames from a structured TikTok video.",
            "Identify the visual hook (first frame), the pacing, and the key visual elements.",
            "Tell me WHY this is visually engaging in one sentence.",
            *image_parts 
        ]

        try:
            response = self.client.generate_content(prompt)
            return {
                "visual_analysis": response.text.strip(),
                "frames_analyzed": len(frames)
            }
        except Exception as e:
            if "429" in str(e):
                logger.warning("Oracle Visual Cortex Rate Limited (429)")
                return {
                    "visual_analysis": "Oracle Visual Cortex is currently overwhelmed (Rate Limit). Try again later.",
                    "frames_analyzed": len(frames),
                    "status": "rate_limited"
                }

            logger.error(f"Visual Analysis Failed: {e}")
            return {"error": str(e)}
        finally:
            # 🧹 CLEANUP: Delete extracted frames to prevent disk bloat
            try:
                for f in frames:
                    if os.path.exists(f):
                        os.remove(f)
            except Exception as cleanup_err:
                logger.warning(f"Failed to cleanup frames: {cleanup_err}")

visual_cortex = VisualCortex()
