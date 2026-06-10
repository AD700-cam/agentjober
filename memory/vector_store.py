import os
import uuid
import time
import chromadb
from tools.embeddings import get_embedding

# Paths to databases
DB_PATH = "memory/vector_db"

# Initialize persistent ChromaDB client
client = None
interview_collection = None
career_collection = None
jobs_collection = None

def _get_client():
    """Lazy initialization of ChromaDB client to ensure pip install finishes before first import/use."""
    global client, interview_collection, career_collection, jobs_collection
    if client is None:
        os.makedirs(DB_PATH, exist_ok=True)
        client = chromadb.PersistentClient(path=DB_PATH)
        interview_collection = client.get_or_create_collection(name="interview_history")
        career_collection = client.get_or_create_collection(name="career_memory")
        jobs_collection = client.get_or_create_collection(name="job_listings")
    return client, interview_collection, career_collection, jobs_collection

def save_scraped_job(title: str, company: str, location: str, description: str, date: str):
    """Saves a scraped job listing and its embedded representation to the job_listings collection."""
    _, _, _, jobs_coll = _get_client()
    
    document_text = (
        f"Job Title: {title}\n"
        f"Company: {company}\n"
        f"Location: {location}\n"
        f"Description: {description}"
    )
    
    job_id = f"job_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    vector = get_embedding(document_text, task_type="retrieval_document")
    
    metadata = {
        "title": title,
        "company": company,
        "location": location,
        "date": date,
        "type": "job_listing"
    }
    
    jobs_coll.add(
        ids=[job_id],
        embeddings=[vector],
        documents=[document_text],
        metadatas=[metadata]
    )

def search_matching_jobs(profile_skills: list[str], n_results: int = 5) -> list[dict]:
    """Queries job listings collection using profile skills as context and returns relevant jobs."""
    _, _, _, jobs_coll = _get_client()
    skills_query = ", ".join(profile_skills)
    query_vector = get_embedding(skills_query, task_type="retrieval_query")
    
    try:
        results = jobs_coll.query(
            query_embeddings=[query_vector],
            n_results=n_results
        )
        
        matched_jobs = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for i in range(len(ids)):
            matched_jobs.append({
                "id": ids[i],
                "document": documents[i],
                "metadata": metadatas[i],
                "score": 1.0 - distances[i] if i < len(distances) else 0.5  # Convert distance to similarity score
            })
        return matched_jobs
    except Exception as e:
        print(f"[Vector Store] Error searching jobs: {e}")
        return []

def save_interview_qa(role: str, question: str, answer: str, feedback: str):
    """Saves a single Q&A session with its feedback into the ChromaDB collection."""
    _, coll, _, _ = _get_client()
    
    document_text = (
        f"Role: {role}\n"
        f"Question: {question}\n"
        f"Answer: {answer}\n"
        f"Feedback: {feedback}"
    )
    
    # Generate unique ID and embedding vector
    doc_id = f"int_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    vector = get_embedding(document_text, task_type="retrieval_document")
    
    metadata = {
        "role": role,
        "timestamp": time.time(),
        "type": "interview_qa"
    }
    
    coll.add(
        ids=[doc_id],
        embeddings=[vector],
        documents=[document_text],
        metadatas=[metadata]
    )

def get_all_interview_history() -> list[str]:
    """Retrieves all past interview Q&A and feedback documents."""
    _, coll, _, _ = _get_client()
    results = coll.get()
    return results.get("documents", [])

def search_interview_history(query: str, n_results: int = 3) -> list[str]:
    """Searches past interview history semantically based on a query."""
    _, coll, _, _ = _get_client()
    query_vector = get_embedding(query, task_type="retrieval_query")
    
    results = coll.query(
        query_embeddings=[query_vector],
        n_results=n_results
    )
    # Return matched documents list
    return [doc for sublist in results.get("documents", []) for doc in sublist]
