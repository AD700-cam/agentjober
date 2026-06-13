import sys
sys.path.insert(0, ".")
from scrapers.jobicy_scraper import scrape_jobicy

jobs = scrape_jobicy(max_jobs=5)
print(f"\n=== Got {len(jobs)} jobs ===")
for j in jobs[:5]:
    print(f"  {j['title']} @ {j['company']}")
    print(f"    URL: {j['url']}")
    print()
