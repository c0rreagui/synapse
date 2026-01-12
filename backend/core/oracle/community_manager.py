import logging
from core.oracle.client import oracle_client

logger = logging.getLogger(__name__)

class CommunityManager:
    """
    Handles community engagement automation.
    Uses the Oracle (LLM) to generate context-aware replies to comments.
    """
    
    def __init__(self):
        self.client = oracle_client

    def generate_reply(self, comment_text: str, tone: str = "Witty/Engaging", context: str = "") -> str:
        """
        Generates a reply to a specific comment.
        
        Args:
            comment_text (str): The user's comment.
            tone (str): Desired tone (e.g., "Hater Neutralizer", "Fan Appreciation", "Sales").
            context (str): Optional context about the video/post.
            
        Returns:
            str: The generated reply.
        """
        if not comment_text:
            return ""

        prompt = f"""
        You are a social media community manager for a viral TikTok account.
        Your goal is to reply to comments to boost engagement and build community.
        
        COMMENT: "{comment_text}"
        VIDEO CONTEXT: "{context}"
        DESIRED TONE: {tone}
        
        INSTRUCTIONS:
        - Keep it short (under 15 words usually).
        - Match the language of the comment (Portuguese or English). Default to PT-BR if unsure.
        - If the tone is 'Hater Neutralizer', be witty but not abusive.
        - If the tone is 'Sales', subtly guide to the link in bio.
        - OUTPUT ONLY THE REPLY TEXT. NO QUOTES.
        """
        
        try:
            response = self.client.generate_content(prompt)
            reply = response.text.strip().replace('"', '')
            return reply
        except Exception as e:
            logger.error(f"❌ CommunityManager Failed: {e}")
            return "🔥" # Fallback safe reply

community_manager = CommunityManager()
