import time
import os
import base64
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class OracleClient:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 0.5 # Groq is fast
        self.provider = "groq"
        self.client = None

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("❌ OracleClient Crítico: GROQ_API_KEY não encontrada!")
            raise Exception("GROQ_API_KEY Missing")
            
        try:
            self.client = Groq(api_key=self.api_key)
            print("OracleClient: Connected to Groq (Llama 3.3 & 3.2 Vision)")
        except Exception as e:
            print(f"Groq Init Failed: {e}")
            self.client = None

    def _enforce_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def generate_content(self, prompt_input):
        """
        Unified wrapper for Groq models.
        Routes to Vision model if input contains images.
        """
        if not self.client:
             raise Exception("Oracle Offline: Groq Client not initialized.")

        self._enforce_rate_limit()

        # Check for Vision Payload (PIL Image)
        is_vision = False
        if isinstance(prompt_input, list):
            for item in prompt_input:
                if hasattr(item, "save"): # PIL Image detection
                    is_vision = True
                    break
        
        try:
            return self._generate_groq(prompt_input, is_vision)
        except Exception as e:
            print(f"Groq Generation Error: {e}")
            raise e

    def _generate_groq(self, prompt_input, is_vision: bool):
        messages = []
        # Default Text Model: Llama 3.3 70B (Reliable & Fast)
        model = "llama-3.3-70b-versatile" 

        if is_vision:
            # Vision Model: Llama 4 Scout (Preview)
            # ID confirmado via documentação Groq (22/01/2026)
            model = "meta-llama/llama-4-scout-17b-16e-instruct" 
            
            content_payload = []
            
            # Flat input list handling
            input_list = prompt_input if isinstance(prompt_input, list) else [prompt_input]
            
            for item in input_list:
                if isinstance(item, str):
                    content_payload.append({"type": "text", "text": item})
                elif hasattr(item, "save"): # Is PIL Image
                    import io
                    buffered = io.BytesIO()
                    item.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    content_payload.append({
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}
                    })
            
            messages = [{"role": "user", "content": content_payload}]
        else:
            # Text Only Mode
            text_content = ""
            if isinstance(prompt_input, list):
                text_content = "\n".join([str(x) for x in prompt_input if isinstance(x, str)])
            else:
                text_content = str(prompt_input)
                
            messages = [{"role": "user", "content": text_content}]

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
        
        # JSON Mode only strict for Text models currently in reusable way
        # But Llama 3.3 supports response_format={"type": "json_object"} nicely
        if not is_vision and "json" in str(messages).lower():
             params["response_format"] = {"type": "json_object"}

        completion = self.client.chat.completions.create(**params)
        
        # Mocking the Gemini Response Object structure for compatibility
        class MockResponse:
            def __init__(self, text): self.text = text
            
        return MockResponse(completion.choices[0].message.content)

    def ping(self):
        try:
            response = self.generate_content("Say 'Hello World'")
            return {"message": response.text.strip(), "provider": self.provider}
        except Exception as e:
            return {"error": str(e)}

oracle_client = OracleClient()
