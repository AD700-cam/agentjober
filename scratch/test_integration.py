"""Quick integration test: scrape from all sources, check readiness scoring, verify URL resolution."""
import sys
sys.path.insert(0, ".")

print("=" * 60)
print("INTEGRATION TEST: Multi-Source Scraper + Scoring")
print("=" * 60)

# Test 1: RemoteOK Scraper
print("\n--- Test 1: RemoteOK Scraper ---")
try:
    from scrapers.remoteok_scraper import scrape_remoteok
    rok_jobs = scrape_remoteok(max_jobs=3)
    print(f"  Result: {len(rok_jobs)} jobs scraped")
    for j in rok_jobs[:2]:
        print(f"    {j['title']} @ {j['company']} | URL: {j['url'][:60]}...")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: Jobicy Scraper
print("\n--- Test 2: Jobicy Scraper ---")
try:
    from scrapers.jobicy_scraper import scrape_jobicy
    jcy_jobs = scrape_jobicy(max_jobs=3)
    print(f"  Result: {len(jcy_jobs)} jobs scraped")
    for j in jcy_jobs[:2]:
        print(f"    {j['title']} @ {j['company']} | URL: {j['url'][:60]}...")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: Readiness Scoring (keyword fallback)
print("\n--- Test 3: Keyword-Based Readiness Scoring ---")
try:
    from agents.readiness_agent import _keyword_fallback_score
    from tools.load_profile import load_profile
    
    profile = load_profile("data/master_profile.json")
    
    # Test with a matching job
    good_job = "We are looking for a Frontend Developer with React, TypeScript, and Next.js experience. Knowledge of JavaScript, PWA, and Prisma is a plus."
    score_good = _keyword_fallback_score(profile, good_job)
    print(f"  Good match job score: {score_good['match_score']}%")
    print(f"    Strengths: {score_good['strengths'][:5]}")
    
    # Test with a non-matching job
    bad_job = "We need a Marketing Manager with expertise in SEO, Google Ads, and content marketing."
    score_bad = _keyword_fallback_score(profile, bad_job)
    print(f"  Bad match job score: {score_bad['match_score']}%")
    print(f"    Strengths: {score_bad['strengths'][:5]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 4: URL Resolver
print("\n--- Test 4: URL Resolver ---")
try:
    from tools.url_resolver import is_ats_url
    tests = [
        ("https://boards.greenhouse.io/company/jobs/123", True),
        ("https://jobs.lever.co/company/xyz", True),
        ("https://www.ycombinator.com/companies/test", False),
        ("https://remoteok.com/remote-jobs/some-job", False),
    ]
    for url, expected in tests:
        result = is_ats_url(url)
        status = "✅" if result == expected else "❌"
        print(f"  {status} is_ats_url({url[:50]}...) = {result} (expected {expected})")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("INTEGRATION TEST COMPLETE")
print("=" * 60)
