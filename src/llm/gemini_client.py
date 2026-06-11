# src/llm/gemini_client.py

import os
import time
import httpx
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# Initialize Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_resume(prompt: str) -> str:
    """Generates resume content based on a detailed tailoring prompt with robust transient error retries and model fallbacks."""
    models_to_try = ["gemini-2.5-pro", "gemini-3.5-flash", "gemini-2.5-flash"]
    
    for model_name in models_to_try:
        max_retries = 3
        backoff_sec = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                err_msg = str(e)
                # Check for quota limits or resource exhaustion errors
                if "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower() or "429" in err_msg:
                    print(f"[Gemini Client] Model {model_name} quota exceeded. Trying fallback model...")
                    break  # Break out of retry loop to move to the next model
                
                # If it's a network issue, retry
                if isinstance(e, (httpx.HTTPError, ConnectionError, OSError)):
                    if attempt == max_retries - 1:
                        print(f"[Gemini Client Error] Model {model_name} failed after {max_retries} attempts: {e}")
                        break
                    print(f"[Gemini Client Warning] Connection issue (attempt {attempt+1}/{max_retries}): {e}. Retrying in {backoff_sec}s...")
                    time.sleep(backoff_sec)
                    backoff_sec *= 2
                else:
                    # Raise non-transient exceptions
                    print(f"[Gemini Client Error] Model {model_name} encountered error: {e}")
                    break
                    
    raise RuntimeError("All configured Gemini models failed to generate content (likely due to quota limits).")
