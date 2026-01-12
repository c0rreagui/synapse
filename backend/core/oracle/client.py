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
        self.min_interval = 2.0 # Groq is faster/higher limits, keeping a small buffer
        self.provider = "gemini"
        
        # 1. Try Groq First (User Preference)
        self.groq_key = os.getenv("GROQ_API_KEY")
        if self.groq_key:
            try:
                self.groq_client = Groq(api_key=self.groq_key)
                self.provider = "groq"
                print("🔮 OracleClient: Connected to Groq (Llama 3.2 Vision / 3.3 70B)")
                return
            except Exception as e:
                print(f"⚠️ Groq Init Failed: {e}. Falling back to Gemini.")

        # 2. Fallback to Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ OracleClient Error: No API Keys found (GEMINI or GROQ).")
            self.model = None
            return

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
        Unified wrapper for Gemini and Groq.
        Input: 
          - str: Text prompt
          - list: Multimodal prompt [text, image_obj, ...]
        Output:
          - object with .text attribute
        """
        self._enforce_rate_limit()

        if self.provider == "groq":
            return self._generate_groq(prompt_input)
        else:
            if not self.model: raise Exception("Oracle Offline")
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
            model = "llama-3.2-11b-vision-preview"
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

        completion = self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            response_format={"type": "json_object"},
            stream=False,
            stop=None,
        )
        
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
