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
            print("OracleClient: Connected to Groq (Llama 3.3 & Llama 4 Maverick Vision)")
        except Exception as e:
            print(f"Groq Init Failed: {e}")
            self.client = None

    def _enforce_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def generate_content(self, prompt_input, **kwargs):
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
                if hasattr(item, "save") or (isinstance(item, dict) and item.get("type") == "image_url"): 
                    is_vision = True
                    break
        
        try:
            return self._generate_groq(prompt_input, is_vision, **kwargs)
        except Exception as e:
            print(f"Groq Generation Error: {e}")
            raise e

    def _generate_groq(self, prompt_input, is_vision: bool, **kwargs):
        messages = []
        # Helper to execute with fallback
        # UPDATED: Check for model override in kwargs
        primary_model = kwargs.get("model", "llama-3.3-70b-versatile")
        
        # If user explicitly requested a model, don't use fallback logic normally,
        # unless it's the default one where we want fallback safety.
        # For now, let's keep the fallback for reliability.
        models_to_try = [primary_model]
        
        # Add fallbacks only if using default and not forced
        if primary_model == "llama-3.3-70b-versatile" and not is_vision:
             models_to_try.append("llama-3.1-8b-instant")
        
        if is_vision:
             # Vision Model: Llama 4 Maverick (Updated: 2026-02-04)
             models_to_try = ["meta-llama/llama-4-maverick-17b-128e-instruct"]

             # [SYN-SMART] Respect User Choice if it's a known Vision Model
             req_model = kwargs.get("model", "").lower()
             if req_model and ("scout" in req_model or "maverick" in req_model or "llama-4" in req_model):
                 models_to_try = [kwargs["model"]]  

        # 1. Buid Messages (Once, as they don't depend on model usually, unless Vision specific logic needed)
        # However, Vision model is specific.
        
        # We build the content payload first
        content_payload = []
        text_content = ""
        
        if is_vision:
            # Flat input list handling
            input_list = prompt_input if isinstance(prompt_input, list) else [prompt_input]
            
            for item in input_list:
                if isinstance(item, dict):
                    # Direct payload pass-through (e.g. for image_url with base64)
                    content_payload.append(item)
                elif isinstance(item, str):
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
            if isinstance(prompt_input, list):
                text_content = "\n".join([str(x) for x in prompt_input if isinstance(x, str)])
            else:
                text_content = str(prompt_input)
            messages = [{"role": "user", "content": text_content}]

        last_error = None
        
        for model in models_to_try:
            # Prepare params with defaults
            params = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_completion_tokens": 1024,
                "top_p": 1,
                "stream": False,
                "stop": None,
            }
            
            # Override with kwargs (e.g., temperature from MindFaculty)
            # [SYN-FIX] Protect 'model' from being overwritten if we selected a specific one (like Vision)
            if "model" in kwargs:
                # We want to keep other kwargs but respect the loop model
                kwargs_copy = kwargs.copy()
                del kwargs_copy["model"]
                params.update(kwargs_copy)
            else:
                params.update(kwargs)
            
            # JSON Mode only strict for Text models currently in reusable way
            # But Llama 3.3 supports response_format={"type": "json_object"} nicely
            if not is_vision and "json" in str(messages).lower() and "response_format" not in params:
                 params["response_format"] = {"type": "json_object"}

            try:
                completion = self.client.chat.completions.create(**params)
                
                # Mocking the Gemini Response Object structure for compatibility
                class MockResponse:
                    def __init__(self, text): self.text = text
                    
                return MockResponse(completion.choices[0].message.content)
            
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str or "429" in error_str:
                    print(f"⚠️ Rate Limit hit on {model}. Retrying with fallback (if avail)...")
                    last_error = e
                    time.sleep(1) # Backoff
                    continue # Try next model
                elif any(x in error_str for x in ["500", "502", "503", "504", "connection", "timeout"]):
                     print(f"⚠️ Transient Error ({e}) on {model}. Retrying...")
                     last_error = e
                     time.sleep(2)
                     # Retry same model once? or continue?
                     # Simple logic: If we have multiple models, switching is safer. 
                     # If we are on the last model, we might want to retry it.
                     # For now, continue to next fallback if available.
                     continue
                else:
                    raise e # Client errors (400, 401) fail immediately
                    
        # If loop finishes without return
        if last_error:
            raise last_error

    def transcribe_audio(self, file_path_or_buffer, model="whisper-large-v3", language="pt"):
        """
        Transcribes audio/video file using Groq Whisper.
        """
        if not self.client:
             raise Exception("Oracle Offline: Groq Client not initialized.")
        
        self._enforce_rate_limit()

        try:
             # Handle file path vs buffer
             if isinstance(file_path_or_buffer, str):
                 file_obj = open(file_path_or_buffer, "rb")
             else:
                 # Assume it's a file-like object (BytesIO or SpooledTemporaryFile)
                 file_obj = file_path_or_buffer
            
             transcription = self.client.audio.transcriptions.create(
                 file=(os.path.basename(getattr(file_obj, 'name', 'audio.mp4')), file_obj.read()),
                 model=model,
                 response_format="json",
                 language=language,
                 temperature=0.0
             )
             
             # Close if we opened it
             if isinstance(file_path_or_buffer, str):
                 file_obj.close()
                 
             return transcription.text
        except Exception as e:
             print(f"Groq Transcription Error: {e}")
             raise e

    def ping(self):
        try:
            response = self.generate_content("Say 'Hello World'")
            return {"message": response.text.strip(), "provider": self.provider}
        except Exception as e:
            return {"error": str(e)}

    def is_online(self):
        return self.client is not None

    def get_engine_name(self):
        return "groq-llama-3.3-70b"

oracle_client = OracleClient()
