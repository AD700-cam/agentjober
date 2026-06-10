import os
import re
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# Force UTF-8 encoding support
import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Import database module safely
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from memory.vector_store import save_scraped_job
    HAS_DB = True
except ImportError:
    HAS_DB = False

JSON_STORE_PATH = os.path.join(project_root, "scrapers", "job_store.json")

def clean_company_name(name: str) -> str:
    """Removes YC batch info and metadata like 'Airbnb (YC W09)' -> 'Airbnb'."""
    name = re.sub(r'\s*\([^)]*\)\s*', '', name)
    name = re.sub(r'\s*\[[^\]]*\]\s*', '', name)
    return name.strip()

def scrape_jobs(max_jobs: int = 15):
    """Scrapes latest jobs from Hacker News Jobs, saves to JSON, and indexes in ChromaDB."""
    print("=== Launching Playwright Scraper ===")
    
    scraped_jobs = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print("Navigating to Hacker News Jobs (crawler-friendly)...")
            page.goto("https://news.ycombinator.com/jobs", timeout=60000)
            
            # Select job anchors on HN
            # The structure is typically .titleline > a
            job_anchors = page.query_selector_all(".titleline > a")
            
            print(f"Found {len(job_anchors)} job listings. Scraping first {min(max_jobs, len(job_anchors))}...")
            
            # Sub-page limit for full text post scraping to keep it fast
            text_post_count = 0
            
            for idx, anchor in enumerate(job_anchors[:max_jobs], 1):
                try:
                    text = anchor.inner_text().strip()
                    href = anchor.get_attribute("href") or ""
                    
                    # Parsed defaults
                    company = "Hacker News Job"
                    title = text
                    location = "Remote / Onsite"
                    posted_date = datetime.today().strftime('%Y-%m-%d')
                    
                    # Split company name & title
                    for delimiter in ["is hiring", "Is hiring", "Is Hiring", "Hiring", "hiring", "seeks", "joins"]:
                        if delimiter in text:
                            parts = text.split(delimiter, 1)
                            company = clean_company_name(parts[0])
                            title = parts[1].strip()
                            # Clean leading separators
                            title = re.sub(r'^[\s\:\-]+', '', title).strip()
                            break
                    
                    description = ""
                    # If it's a text post (starts with item?id=), scrape the body details
                    if href.startswith("item?id=") and text_post_count < 3:
                        text_post_count += 1
                        print(f"  [{idx}] Fetching text post body for: {company}...")
                        sub_page = context.new_page()
                        try:
                            sub_page.goto(f"https://news.ycombinator.com/{href}", timeout=30000)
                            toptext = sub_page.query_selector(".toptext")
                            if toptext:
                                description = toptext.inner_text().strip()
                        except Exception as e:
                            print(f"    Failed to load sub-page: {e}")
                        finally:
                            sub_page.close()
                            
                    if not description:
                        description = f"Job listing for {title} at {company}. Check listing page for full application process: {href if href.startswith('http') else 'https://news.ycombinator.com/' + href}"
                    
                    job_record = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "posted_date": posted_date,
                        "description": description,
                        "url": href if href.startswith("http") else f"https://news.ycombinator.com/{href}"
                    }
                    
                    scraped_jobs.append(job_record)
                    print(f"  [{idx}] Scraped: '{title}' at '{company}'")
                    
                    # Pushes to Vector Memory for profile matching
                    if HAS_DB:
                        try:
                            save_scraped_job(title, company, location, description, posted_date)
                        except Exception as e:
                            print(f"    Vector store save failed: {e}")
                            
                except Exception as entry_err:
                    print(f"  Error processing job index {idx}: {entry_err}")
                    
        except Exception as e:
            print(f"Scraper failed during page execution: {e}")
        finally:
            browser.close()
            
    # Save to local JSON backup
    try:
        os.makedirs(os.path.dirname(JSON_STORE_PATH), exist_ok=True)
        with open(JSON_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(scraped_jobs, f, indent=2)
        print(f"\n[Success] Scraped {len(scraped_jobs)} jobs. Saved database to '{JSON_STORE_PATH}'!")
    except Exception as e:
        print(f"Failed to write json backup: {e}")
        
    return scraped_jobs

if __name__ == "__main__":
    scrape_jobs()
