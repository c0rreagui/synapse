"""
Hearing Faculty - Audio Perception
The ears of the Oracle. Transcribes audio and video to text.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HearingFaculty:
    """
    The Hearing: Audio Analysis Engine.
    Transcribes audio and video content to text using Groq Whisper.
    """

    def __init__(self, client):
        self.client = client

    async def transcribe(self, file_source) -> Dict[str, Any]:
        """
        Transcribes an audio or video file.
        Input: file_path (str) or file-like object.
        """
        if not self.client:
            return {"error": "Oracle Hearing is offline"}

        try:
            logger.info("[HEARING] Transcribing audio source...")
            text = self.client.transcribe_audio(file_source)
            logger.info(f"[HEARING] Transcription success: {len(text)} chars")
            return {"text": text, "faculty": "hearing"}
        except Exception as e:
            logger.error(f"[ERROR] Oracle.Hearing transcription failed: {e}")
            return {"error": str(e)}
