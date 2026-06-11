import os
import json
import hashlib
from tools.load_profile import load_profile
from tools.embeddings import get_embedding, cosine_similarity

# Local paths
INDEX_PATH = "data/memory_index.json"
PROFILE_PATH = "data/master_profile.json"

# High-speed index cache variables
_INDEX_CACHE = None
_INDEX_MTIME = None

def get_cached_index_data(path=INDEX_PATH) -> dict:
    """Loads and caches index JSON data, automatically re-reading only if file changes on disk."""
    global _INDEX_CACHE, _INDEX_MTIME
    if not os.path.exists(path):
        return {}
    try:
        current_mtime = os.path.getmtime(path)
        if _INDEX_CACHE is not None and _INDEX_MTIME == current_mtime:
            return _INDEX_CACHE
        with open(path, "r", encoding="utf-8") as f:
            _INDEX_CACHE = json.load(f)
            _INDEX_MTIME = current_mtime
            return _INDEX_CACHE
    except Exception:
        return {}

def get_profile_hash(profile: dict) -> str:
    """Generates an MD5 hash of the profile dictionary to track changes."""
    profile_str = json.dumps(profile, sort_keys=True)
    return hashlib.md5(profile_str.encode("utf-8")).hexdigest()

def chunk_profile(profile: dict) -> list[str]:
    """Splits the candidate profile into discrete semantic text chunks."""
    chunks = []
    
    # 1. Personal Info
    p_info = profile.get("personal_info", {})
    if p_info:
        chunks.append(
            f"Candidate Personal Information:\n"
            f"- Name: {p_info.get('name', 'N/A')}\n"
            f"- Email: {p_info.get('email', 'N/A')}\n"
            f"- Phone: {p_info.get('phone', 'N/A')}\n"
            f"- Location: {p_info.get('location', 'N/A')}"
        )
        chunks.append(
            f"Candidate Web Profiles & Websites:\n"
            f"- Portfolio: {p_info.get('portfolio', 'N/A')}\n"
            f"- LinkedIn: {p_info.get('linkedin', 'N/A')}\n"
            f"- GitHub: {p_info.get('github', 'N/A')}"
        )

    # 2. Education
    education = profile.get("education", [])
    for edu in education:
        degree = edu.get("degree", "N/A")
        inst = edu.get("institution", "N/A")
        univ = edu.get("university", "N/A")
        end = edu.get("end_year", "N/A")
        spec = edu.get("specialization", "N/A")
        chunks.append(
            f"Candidate Education & Academic Background:\n"
            f"- Degree: {degree}\n"
            f"- Institution: {inst}\n"
            f"- University: {univ}\n"
            f"- Graduation Year: {end}\n"
            f"- Focus/Specialization: {spec}"
        )

    # 3. Skills (divided by category to keep chunks distinct)
    skills = profile.get("skills", {})
    if skills:
        for category, items in skills.items():
            if items:
                items_str = ", ".join(items)
                chunks.append(
                    f"Candidate Skill Category ({category.replace('_', ' ').title()}): {items_str}"
                )

    # 4. Work Experience
    experience = profile.get("work_experience", [])
    for exp in experience:
        company = exp.get("company", "N/A")
        role = exp.get("role", "N/A")
        start = exp.get("start_date", "")
        end = exp.get("end_date", "")
        dates = f" ({start} - {end})" if start or end else ""
        resps = "\n  * ".join(exp.get("responsibilities", []))
        achieves = "\n  * ".join(exp.get("achievements", []))
        
        chunk_text = (
            f"Candidate Work Experience:\n"
            f"- Company: {company}{dates}\n"
            f"- Role: {role}\n"
            f"- Responsibilities:\n  * {resps}"
        )
        if achieves:
            chunk_text += f"\n- Key Achievements:\n  * {achieves}"
        chunks.append(chunk_text)

    # 5. Projects
    projects = profile.get("projects", [])
    for proj in projects:
        name = proj.get("project_name", "N/A")
        desc = proj.get("description", "N/A")
        tech = ", ".join(proj.get("technologies", []))
        role = proj.get("role", "N/A")
        features = "\n  * ".join(proj.get("features", []))
        outcomes = "\n  * ".join(proj.get("outcomes", []))
        
        chunk_text = (
            f"Candidate Project Showcase:\n"
            f"- Project Name: {name}\n"
            f"- Role: {role}\n"
            f"- Technologies Used: {tech}\n"
            f"- Description: {desc}\n"
            f"- Key Features:\n  * {features}"
        )
        if outcomes:
            chunk_text += f"\n- Project Outcomes & Impact:\n  * {outcomes}"
        chunks.append(chunk_text)

    return chunks

def build_index(force: bool = False) -> bool:
    """Builds/Updates the local vector database index from the profile JSON."""
    try:
        profile = load_profile(PROFILE_PATH)
    except Exception as e:
        print(f"[Memory Manager] Error loading profile: {e}")
        return False
        
    current_hash = get_profile_hash(profile)
    
    # Check if existing index is fresh
    if not force and os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                index_data = json.load(f)
                if index_data.get("profile_hash") == current_hash:
                    # Index is fresh, no need to rebuild
                    return True
        except Exception:
            pass # If corrupted, rebuild
            
    print("\n[Memory Manager] Memory index is stale or missing. Building semantic index...")
    chunks = chunk_profile(profile)
    indexed_chunks = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"  Embedding chunk {i}/{len(chunks)}...")
        vector = get_embedding(chunk, task_type="retrieval_document")
        indexed_chunks.append({
            "text": chunk,
            "embedding": vector
        })
        
    # Serialize index
    index_data = {
        "profile_hash": current_hash,
        "chunks": indexed_chunks
    }
    
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)
        
    print("[Memory Manager] Semantic memory index created successfully!")
    return True

def search(query: str, top_k: int = 3) -> str:
    """Queries semantic memory using cosine similarity and returns merged relevant context."""
    # Ensure index exists and is built
    build_index()
    
    index_data = get_cached_index_data()
    if not index_data:
        print("[Memory Manager] Failed to load index data.")
        return ""
        
    # Get query embedding
    query_vector = get_embedding(query, task_type="retrieval_query")
    
    # Score each chunk
    scored_chunks = []
    for chunk in index_data.get("chunks", []):
        similarity = cosine_similarity(query_vector, chunk["embedding"])
        scored_chunks.append((similarity, chunk["text"]))
        
    # Sort descending by similarity
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Retrieve top K
    top_results = scored_chunks[:top_k]
    
    # Build context string
    context_blocks = []
    for score, text in top_results:
        # Include a minor header detailing similarity match score for debugging if needed
        context_blocks.append(f"--- (Similarity Match Score: {score:.3f}) ---\n{text}")
        
    return "\n\n".join(context_blocks)
