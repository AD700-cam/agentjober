import httpx

# Test Jobicy API
print("Testing Jobicy API...")

# Try different endpoint formats
urls = [
    "https://jobicy.com/api/v2/remote-jobs?count=10",
    "https://jobicy.com/api/v2/remote-jobs?count=10&tag=developer",
    "https://jobicy.com/api/v2/remote-jobs",
]

for url in urls:
    try:
        r = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15.0, follow_redirects=True)
        print(f"\n  URL: {url}")
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            jobs = data.get("jobs", [])
            print(f"  Jobs: {len(jobs)}")
            for j in jobs[:3]:
                print(f"    - {j.get('jobTitle', '?')} @ {j.get('companyName', '?')}")
            break
        else:
            print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
