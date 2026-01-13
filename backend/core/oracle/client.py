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

        # 3. Fallback to Mock if NO keys
        if not self.groq_client and not self.model:
            self.provider = "mock"
            print("⚠️ OracleClient: No API Keys found. Enabled MOCK MODE for demo.")

    def _enforce_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def generate_content(self, prompt_input):
        """
        Unified wrapper: Routes Vision -> Gemini, Text -> Groq (if avail).
        """
        self._enforce_rate_limit()

        # Check for Vision Payload (PIL Image)
        is_vision = False
        if isinstance(prompt_input, list):
            for item in prompt_input:
                if hasattr(item, "save"): # PIL Image detection
                    is_vision = True
                    break
        
        # Mock Mode
        if self.provider == "mock":
            class MockResponse:
                def __init__(self, text): self.text = text
            
            # Simple keyword matching to guess intent
            p_str = str(prompt_input).lower()
            
            if "viral" in p_str and "caption" in p_str:
                import json
                return MockResponse(json.dumps({
                    "suggested_caption": "😱 Você sabia disso? #curiosidades",
                    "hashtags": ["#viral", "#fy", "#tiktok", "#growth", "#mockData"],
                    "viral_score": 88,
                    "viral_reason": "High engagement potential detected by (Mock) AI."
                }))
            elif "score" in p_str and "avatar" in p_str:
                 import json
                 return MockResponse(json.dumps({
                    "score": 75,
                    "impression": "Perfil Profissional (Mock)",
                    "pros": ["Boa iluminação", "Sorriso confiante"],
                    "cons": ["Fundo muito poluído"],
                    "verdict": "Profissional"
                }))
            else:
                 return MockResponse("This is a mock response from Oracle. Please configure API Keys.")

        # 1. Vision Request -> Try Gemini First (Stable)
        if is_vision and self.model:
            try:
                return self.model.generate_content(prompt_input)
            except Exception as e:
                print(f"Gemini Vision Error: {e}. Falling back to Groq.")
                # Fallthrough to Groq

        # 2. Text Request OR Vision Fallback -> Use Groq
        if self.provider == "groq" and self.groq_client:
            try: 
                return self._generate_groq(prompt_input)
            except Exception as gx:
                if is_vision: raise Exception(f"Vision Failed on both Gemini and Groq ({gx})")
                raise gx
        else:
            if not self.model: raise Exception("Oracle Offline (No Providers)")
            # If we are here, Groq failed or not avail, retry Gemini (if not tried yet logic?)
            # Simplified: If Gemini failed earlier, we might loop? 
            # Risk: infinite loop if self.model calls generate_content again? 
            # No, self.model.generate_content call native lib.
            return self.model.generate_content(prompt_input)

    def _generate_groq(self, prompt_input):
        """Groq Implementation using Llama 3 models."""
        messages = []
        model = "llama-3.3-70b-versatile" # Default for text

        # Handle Text-Only vs Multimodal
        if isinstance(prompt_input, str):
            messages = [{"role": "user", "content": prompt_input}]
        elif isinstance(prompt_input, list):
            # Multimodal Logic (Llama 3.2 Vision)
            model = "llama-3.2-90b-vision-preview" # 90B is smarter/stable
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
        
        # Llama 3.2 Vision often errors with response_format={"type": "json_object"}
        # Enable JSON mode only for text models
        if "vision" not in model:
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

oracle_client = OracleClient()
