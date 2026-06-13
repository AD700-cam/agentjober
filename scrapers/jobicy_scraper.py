# scrapers/jobicy_scraper.py
# Free RSS/JSON scraper for Jobicy — remote-only job board, no auth needed

import os
import sys
import json
import httpx
import re
from datetime import datetime

# Force UTF-8 encoding support
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from memory.vector_store import save_scraped_job
    HAS_DB = True
except ImportError:
    HAS_DB = False

# Tech-specific keywords for filtering (strict — must be related to our stack)
TECH_KEYWORDS = [
    "react", "nextjs", "next.js", "typescript", "javascript", "frontend",
    "front-end", "fullstack", "full-stack", "web developer", "node",
    "nodejs", "pwa", "prisma", "vue", "angular", "html", "css",
    "tailwind", "graphql", "rest api", "api developer"
]

# Title must contain one of these to qualify as a dev role
DEV_TITLE_KEYWORDS = [
    "developer", "engineer", "frontend", "fullstack", "full-stack",
    "front-end", "programmer", "software", "web dev", "react",
    "typescript", "javascript", "node", "coding"
]

JSON_STORE_PATH = os.path.join(project_root, "scrapers", "jobicy_jobs.json")


def scrape_jobicy(max_jobs: int = 20) -> list[dict]:
    """Fetches remote job listings from Jobicy's free public API."""
    print("=== Jobicy Scraper: Fetching remote developer jobs ===")
    
    scraped_jobs = []
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        # Jobicy free API endpoint for remote jobs
        api_url = "https://jobicy.com/api/v2/remote-jobs?count=50"
        
        response = httpx.get(api_url, headers=headers, timeout=30.0, follow_redirects=True)
        
        if response.status_code != 200:
            print(f"  Jobicy API returned status {response.status_code}")
            return []
        
        data = response.json()
        jobs = data.get("jobs", [])
        print(f"  Received {len(jobs)} listings from Jobicy API")
        
        matched = 0
        for job in jobs:
            if matched >= max_jobs:
                break
            
            title = job.get("jobTitle", "").strip()
            company = job.get("companyName", "").strip()
            location = job.get("jobGeo", "Remote")
            url = job.get("url", "")
            date = job.get("pubDate", datetime.today().strftime('%Y-%m-%d'))[:10]
            job_type = job.get("jobType", "")
            description = job.get("jobDescription", "")
            salary = job.get("annualSalaryMin", "")
            salary_max = job.get("annualSalaryMax", "")
            
            if not title or not company:
                continue
            
            # Clean HTML from description
            clean_desc = re.sub(r'<[^>]+>', ' ', description)
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            
            # Two-tier relevance check:
            # 1. Title must look like a dev role
            title_lower = title.lower()
            is_dev_role = any(kw in title_lower for kw in DEV_TITLE_KEYWORDS)
            
            # 2. Description or title must mention our tech stack
            combined_text = f"{title} {clean_desc[:500]}".lower()
            has_tech_match = any(kw in combined_text for kw in TECH_KEYWORDS)
            
            if not (is_dev_role or has_tech_match):
                continue
            
            full_description = f"Job Title: {title}\nCompany: {company}\nLocation: {location}\n"
            if job_type:
                full_description += f"Type: {job_type}\n"
            if salary and salary_max:
                full_description += f"Salary: {salary} - {salary_max}\n"
            full_description += f"\n{clean_desc}"
            
            job_record = {
                "title": title,
                "company": company,
                "location": location or "Remote",
                "posted_date": date,
                "description": full_description[:2000],
                "url": url,
                "tags": [],
                "source": "jobicy"
            }
            
            scraped_jobs.append(job_record)
            matched += 1
            print(f"  [{matched}] ✅ {title} @ {company}")
            
            # Save to vector store
            if HAS_DB:
                try:
                    save_scraped_job(title, company, location, full_description[:2000], date)
                except Exception as e:
                    print(f"    Vector store save failed: {e}")
    
    except httpx.TimeoutException:
        print("  ⚠️ Jobicy API request timed out")
    except Exception as e:
        print(f"  ❌ Jobicy scraper error: {e}")
    
    # Save to local JSON backup
    try:
        with open(JSON_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(scraped_jobs, f, indent=2)
        print(f"\n  [Jobicy] Saved {len(scraped_jobs)} relevant remote jobs to '{JSON_STORE_PATH}'")
    except Exception as e:
        print(f"  Failed to write Jobicy JSON backup: {e}")
    
    return scraped_jobs


if __name__ == "__main__":
    results = scrape_jobicy()
    print(f"\nTotal relevant remote jobs found: {len(results)}")
