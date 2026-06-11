import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Testing embedding with model: models/gemini-embedding-001")
try:
    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents="Hello world",
    )
    print(f"Type: {type(response)}")
    print(f"Has 'embeddings': {hasattr(response, 'embeddings')}")
    print(f"Has 'embedding': {hasattr(response, 'embedding')}")
    if hasattr(response, 'embedding'):
        print(f"Embedding values count: {len(response.embedding.values)}")
    elif hasattr(response, 'embeddings'):
        print(f"First embedding values count: {len(response.embeddings[0].values)}")
except Exception as e:
    print(f"Error: {e}")
