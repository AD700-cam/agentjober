import os
import sys

# Force UTF-8 encoding support
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scrapers.job_scraper import scrape_jobs
from memory.vector_store import search_matching_jobs
from tools.load_profile import load_profile

def main():
    print("--- Testing Job Scraper and Database Integration ---")
    
    # 1. Run the scraper for a small sample (max 2 jobs) to verify Playwright works
    print("Step 1: Scraping 2 jobs...")
    jobs = scrape_jobs(max_jobs=2)
    print(f"Scraped {len(jobs)} jobs.")
    
    if len(jobs) == 0:
        print("Warning: No jobs scraped. Make sure internet connection is active and HN jobs is reachable.")
    
    # 2. Check JSON backup file
    json_path = os.path.join(project_root, "scrapers", "job_store.json")
    if os.path.exists(json_path):
        print(f"Step 2: JSON store exists at: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                import json
                data = json.load(f)
                print(f"JSON backup contains {len(data)} items.")
            except Exception as e:
                print(f"Failed to parse JSON backup: {e}")
    else:
        print(f"Error: JSON store not found at {json_path}")
        
    # 3. Test querying matching jobs using skills from profile
    print("Step 3: Querying vector store for matches...")
    try:
        profile = load_profile()
        # Extract skills
        skills_dict = profile.get("skills", {})
        skills_list = []
        for cat, items in skills_dict.items():
            if items:
                skills_list.extend(items)
        print(f"Candidate skills: {skills_list}")
        
        matches = search_matching_jobs(skills_list, n_results=3)
        print(f"Found {len(matches)} matching jobs in ChromaDB:")
        for idx, match in enumerate(matches, 1):
            meta = match.get("metadata", {})
            print(f"  Match #{idx}:")
            print(f"    Title: {meta.get('title')}")
            print(f"    Company: {meta.get('company')}")
            print(f"    Similarity Score: {match.get('score'):.3f}")
    except Exception as e:
        print(f"Vector search test failed: {e}")

if __name__ == "__main__":
    main()
