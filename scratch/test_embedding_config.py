import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Testing configured embedding with models/gemini-embedding-001...")
try:
    # Let's try passing as dictionary first
    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents="Hello world",
        config={
            "output_dimensionality": 768,
            "task_type": "RETRIEVAL_DOCUMENT"
        }
    )
    print("Dict configuration worked!")
    print(f"Embedding values count: {len(response.embeddings[0].values)}")
except Exception as e:
    print(f"Dict configuration failed: {e}")

try:
    # Let's try passing as types.EmbedContentConfig
    config = types.EmbedContentConfig(
        output_dimensionality=768,
        task_type="RETRIEVAL_DOCUMENT"
    )
    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents="Hello world",
        config=config
    )
    print("Types object configuration worked!")
    print(f"Embedding values count: {len(response.embeddings[0].values)}")
except Exception as e:
    print(f"Types object configuration failed: {e}")
