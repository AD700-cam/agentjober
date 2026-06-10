import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Shared Gemini Model instance
model = genai.GenerativeModel("gemini-3.5-flash")
