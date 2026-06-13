import sys
sys.path.insert(0, ".")
from scrapers.remoteok_scraper import scrape_remoteok

jobs = scrape_remoteok(max_jobs=5)
print(f"\n=== Got {len(jobs)} jobs ===")
for j in jobs[:5]:
    print(f"  {j['title']} @ {j['company']}")
    print(f"    URL: {j['url']}")
    print(f"    Source: {j.get('source', 'unknown')}")
    print()
