# scrapers/remoteok_scraper.py
# Free JSON API scraper for RemoteOK — no auth, no cost

import os
import sys
import json
import time
import httpx

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

# Skills to filter for (lowercase)
RELEVANT_TAGS = [
    "react", "nextjs", "next.js", "typescript", "javascript", "frontend",
    "front-end", "fullstack", "full-stack", "web developer", "node",
    "nodejs", "web", "software engineer", "developer", "engineer",
    "pwa", "prisma", "trpc", "t3"
]

JSON_STORE_PATH = os.path.join(project_root, "scrapers", "remoteok_jobs.json")


def scrape_remoteok(max_jobs: int = 20) -> list[dict]:
    """Fetches remote job listings from RemoteOK's free JSON API and filters for relevant dev roles."""
    print("=== RemoteOK Scraper: Fetching remote developer jobs ===")
    
    scraped_jobs = []
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        response = httpx.get(
            "https://remoteok.com/api",
            headers=headers,
            timeout=30.0,
            follow_redirects=True
        )
        
        if response.status_code != 200:
            print(f"  RemoteOK API returned status {response.status_code}")
            return []
            
        data = response.json()
        
        # First element is metadata/legal notice, skip it
        jobs = data[1:] if len(data) > 1 else []
        print(f"  Received {len(jobs)} total listings from API")
        
        matched = 0
        for job in jobs:
            if matched >= max_jobs:
                break
                
            # Extract fields
            title = job.get("position", "").strip()
            company = job.get("company", "").strip()
            tags = [t.lower() for t in job.get("tags", [])]
            description = job.get("description", "").strip()
            location = job.get("location", "Remote")
            url = job.get("url", "")
            date = job.get("date", "")[:10]  # YYYY-MM-DD
            salary_min = job.get("salary_min", "")
            salary_max = job.get("salary_max", "")
            
            if not title or not company:
                continue
            
            # Build apply URL — RemoteOK uses /remote-jobs/<id> pattern
            job_id = job.get("id", "")
            slug = job.get("slug", "")
            if url:
                apply_url = url if url.startswith("http") else f"https://remoteok.com{url}"
            elif slug:
                apply_url = f"https://remoteok.com/remote-jobs/{slug}"
            else:
                apply_url = f"https://remoteok.com/remote-jobs/{job_id}"
                
            # Check relevance — match tags or title against our skill keywords
            combined_text = f"{title} {' '.join(tags)} {description[:500]}".lower()
            is_relevant = any(tag in combined_text for tag in RELEVANT_TAGS)
            
            if not is_relevant:
                continue
                
            # Build description with useful details
            full_description = f"Job Title: {title}\nCompany: {company}\nLocation: {location}\n"
            if salary_min and salary_max:
                full_description += f"Salary: ${salary_min} - ${salary_max}\n"
            full_description += f"Tags: {', '.join(tags)}\n\n{description}"
            
            # Clean HTML from description
            import re
            full_description = re.sub(r'<[^>]+>', ' ', full_description)
            full_description = re.sub(r'\s+', ' ', full_description).strip()
            
            job_record = {
                "title": title,
                "company": company,
                "location": location or "Remote",
                "posted_date": date,
                "description": full_description[:2000],  # Cap description length
                "url": apply_url,
                "tags": tags,
                "source": "remoteok"
            }
            
            scraped_jobs.append(job_record)
            matched += 1
            print(f"  [{matched}] ✅ {title} @ {company} ({', '.join(tags[:4])})")
            
            # Save to vector store
            if HAS_DB:
                try:
                    save_scraped_job(title, company, location, full_description[:2000], date)
                except Exception as e:
                    print(f"    Vector store save failed: {e}")
    
    except httpx.TimeoutException:
        print("  ⚠️ RemoteOK API request timed out")
    except Exception as e:
        print(f"  ❌ RemoteOK scraper error: {e}")
    
    # Save to local JSON backup
    try:
        with open(JSON_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(scraped_jobs, f, indent=2)
        print(f"\n  [RemoteOK] Saved {len(scraped_jobs)} relevant remote jobs to '{JSON_STORE_PATH}'")
    except Exception as e:
        print(f"  Failed to write RemoteOK JSON backup: {e}")
    
    return scraped_jobs


if __name__ == "__main__":
    results = scrape_remoteok()
    print(f"\nTotal relevant remote jobs found: {len(results)}")
