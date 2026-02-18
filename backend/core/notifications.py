
import aiohttp
import logging
from .config import DISCORD_WEBHOOK_URL

logger = logging.getLogger("Notifications")

class NotificationManager:
    def __init__(self):
        self.webhook_url = DISCORD_WEBHOOK_URL

    async def send_alert(self, title: str, message: str, color: int = 0xFF0000):
        """
        Sends an embed alert to Discord.
        Color Red: 0xFF0000
        Color Orange: 0xFFA500
        Color Green: 0x00FF00
        """
        if not self.webhook_url:
            logger.warning("Notification skipped: DISCORD_WEBHOOK_URL not set.")
            return

        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": color
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status not in [200, 204]:
                        logger.error(f"Failed to send notification: {response.status}")
                    else:
                        logger.info(f"🔔 Notification sent: {title}")
        except Exception as e:
            logger.error(f"Notification Error: {e}")

notification_manager = NotificationManager()
