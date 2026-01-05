import requests
from app.core.config import settings
import os

class LinkedInPoster:
    """
    Handles posting to LinkedIn via the official API.
    Supports: Text, Image, Video.
    """
    API_URL = "https://api.linkedin.com/v2"

    def __init__(self):
        self.access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    
    def get_me(self):
        """Fetches current user profile URN."""
        url = f"{self.API_URL}/me"
        try:
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None

    def register_upload(self, author_urn: str):
        """
        Step 1: Register the upload to get the upload URL.
        """
        url = f"{self.API_URL}/assets?action=registerUpload"
        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                "owner": author_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        resp = requests.post(url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    def post_video(self, video_path: str, caption: str):
        """
        Orchestrates the video post flow:
        1. Get User URN
        2. Register Upload
        3. Upload Binary
        4. Create UGC Post
        """
        # Implementation to be completed with proper URN handling
        pass
