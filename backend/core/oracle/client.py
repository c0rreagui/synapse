import time
import os
import base64
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq

load_dotenv()

class OracleClient:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 2.0 
        self.provider = "gemini" # Default fallback
        self.model = None
        self.groq_client = None

        # 1. Init Groq (Text Specialist)
        self.groq_key = os.getenv("GROQ_API_KEY")
        if self.groq_key:
            try:
                self.groq_client = Groq(api_key=self.groq_key)
                self.provider = "groq"
                print("OracleClient: Connected to Groq (Text Engine)")
            except Exception as e:
                print(f"Groq Init Failed: {e}. Falling back to Gemini.")

        # 2. Init Gemini (Vision Specialist & Fallback)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("OracleClient Warning: No GEMINI_API_KEY. Vision features will be limited.")
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            print("🔮 OracleClient: Connected to Gemini (Flash 2.0)")

    def _enforce_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def generate_content(self, prompt_input):
        """
        Unified wrapper: Routes Vision -> Groq (Llama 3.2V), Text -> Groq.
        Gemini is fallback only.
        """
        self._enforce_rate_limit()

        # Check for Vision Payload (PIL Image)
        is_vision = False
        if isinstance(prompt_input, list):
            for item in prompt_input:
                if hasattr(item, "save"): # PIL Image detection
                    is_vision = True
                    break
        
        # 1. Try Groq FIRST for everything (including Vision)
        if self.groq_client:
            try:
                return self._generate_groq(prompt_input)
            except Exception as e:
                print(f"Groq {'Vision' if is_vision else 'Text'} Error: {e}. Falling back to Gemini.")
        
        # 2. Fallback to Gemini
        if self.model:
            try:
                return self.model.generate_content(prompt_input)
            except Exception as e:
                raise Exception(f"Both Groq and Gemini failed: {e}")
        
        raise Exception("Oracle Offline (No API Keys Configured).")

    def _generate_groq(self, prompt_input):
        """Groq Implementation using Llama 4 models."""
        messages = []
        model = "llama-3.3-70b-versatile" # Default for text

        # Handle Text-Only vs Multimodal
        if isinstance(prompt_input, str):
            messages = [{"role": "user", "content": prompt_input}]
        elif isinstance(prompt_input, list):
            # Multimodal Logic (Llama 4 Vision)
            model = "meta-llama/llama-4-scout-17b-16e-instruct" # Llama 4 Scout for Vision
            content_payload = []
            
            for item in prompt_input:
                if isinstance(item, str):
                    content_payload.append({"type": "text", "text": item})
                elif hasattr(item, "save"): # Is PIL Image
                    # Convert PIL to Base64
                    import io
                    buffered = io.BytesIO()
                    item.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    content_payload.append({
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}
                    })
            
            messages = [{"role": "user", "content": content_payload}]

        # Prepare params
        params = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_completion_tokens": 1024,
            "top_p": 1,
            "stream": False,
            "stop": None,
        }
        
        # Llama 4 Vision/Scout models don't support JSON mode
        # Enable JSON mode only for text models
        if "scout" not in model.lower() and "maverick" not in model.lower() and "vision" not in model.lower():
             params["response_format"] = {"type": "json_object"}

        completion = self.groq_client.chat.completions.create(**params)
        
        # Mocking the Gemini Response Object structure for compatibility
        class MockResponse:
            def __init__(self, text): self.text = text
            
        return MockResponse(completion.choices[0].message.content)

    def ping(self):
        try:
            response = self.generate_content("Say 'Hello World' and nothing else.")
            return {"message": response.text.strip(), "provider": self.provider}
        except Exception as e:
            return {"error": str(e)}

    def is_online(self) -> bool:
        """Check if any provider is configured."""
        return self.model is not None or self.groq_client is not None

    def get_engine_name(self) -> str:
        """Return active provider name."""
        return self.provider

oracle_client = OracleClient()
