import math
import google.generativeai as genai
import tools.gemini_client

def get_embedding(text: str, task_type: str = "retrieval_document") -> list[float]:
    """Generates a vector embedding for the given text using Gemini's embedding service."""
    try:
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type=task_type
        )
        return response['embedding']
    except Exception as e:
        print(f"[Embedding Error] Failed to generate embedding: {e}")
        # Return a zero vector fallback to avoid complete application crashes
        return [0.0] * 768

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculates the cosine similarity score between two vector lists."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    
    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0
    
    for a, b in zip(vec_a, vec_b):
        dot_product += a * b
        norm_a += a * a
        norm_b += b * b
        
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
        
    return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))
