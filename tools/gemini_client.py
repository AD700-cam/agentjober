import os
import time
import httpx
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

# Load environment variables
load_dotenv()

# Configure Gemini API client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class GenerativeModelWrapper:
    """A backwards-compatibility wrapper for genai.GenerativeModel using the new google-genai SDK with transient error retries and model fallback."""
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.fallback_models = ["gemini-3.5-flash", "gemini-2.5-flash"]

    def generate_content(self, prompt: str):
        # Build list of models to try
        models_to_try = [self.model_name]
        for fallback in self.fallback_models:
            if fallback not in models_to_try:
                models_to_try.append(fallback)
                
        for current_model in models_to_try:
            max_retries = 3
            backoff_sec = 2
            for attempt in range(max_retries):
                try:
                    return client.models.generate_content(
                        model=current_model,
                        contents=prompt
                    )
                except Exception as e:
                    is_transient = False
                    is_quota = False
                    
                    # Check for google-genai APIErrors
                    if isinstance(e, APIError):
                        # Retry on 503 (Unavailable), 429 (Rate limit), 500 (Internal), 502 (Bad Gateway), 504 (Gateway Timeout)
                        if e.code in [429, 500, 502, 503, 504]:
                            is_transient = True
                        if e.code == 429 or "RESOURCE_EXHAUSTED" in str(e):
                            is_quota = True
                    # Check for standard HTTP or socket network exceptions
                    elif isinstance(e, (httpx.HTTPError, ConnectionError, OSError)):
                        is_transient = True
                    
                    if is_quota:
                        print(f"[Gemini Client Warning] Model {current_model} quota exceeded. Switching to next model...")
                        break  # Break retry loop to switch to next model
                        
                    if is_transient:
                        if attempt == max_retries - 1:
                            raise
                        print(f"[Gemini Client Warning] Transient API error (attempt {attempt+1}/{max_retries}): {e}. Retrying in {backoff_sec}s...")
                        time.sleep(backoff_sec)
                        backoff_sec *= 2
                    else:
                        raise
                        
        raise RuntimeError("All configured Gemini models failed to generate content (likely due to quota limits).")

# Shared Gemini Model instance
model = GenerativeModelWrapper("gemini-3.5-flash")
