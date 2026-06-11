import os
import sys
from dotenv import load_dotenv

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.gemini_client import model

print("Testing model.generate_content('hello') using the new wrapper...")
try:
    response = model.generate_content("hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
