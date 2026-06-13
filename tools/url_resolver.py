# tools/url_resolver.py
# Resolves listing page URLs to actual application form URLs (Greenhouse, Lever, Workable, etc.)

import os
import sys
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Known ATS domain patterns that indicate a direct application form
ATS_PATTERNS = [
    r"boards\.greenhouse\.io",
    r"jobs\.greenhouse\.io",
    r"jobs\.lever\.co",
    r"apply\.workable\.com",
    r"[a-z]+\.ashbyhq\.com",
    r"[a-z]+\.recruitee\.com",
    r"smartrecruiters\.com",
    r"icims\.com",
    r"taleo\.net",
    r"myworkdayjobs\.com",
    r"bamboohr\.com/careers",
    r"breezy\.hr",
    r"jobvite\.com",
]


def is_ats_url(url: str) -> bool:
    """Check if a URL is already a direct ATS application form."""
    url_lower = url.lower()
    for pattern in ATS_PATTERNS:
        if re.search(pattern, url_lower):
            return True
    return False


def resolve_application_url(url: str, page=None) -> str | None:
    """
    Given a job listing URL, attempt to find the direct application form URL.
    
    If `page` is provided (a Playwright Page), uses it to navigate and discover apply links.
    Otherwise, does a simple HTTP fetch to find ATS links in the page HTML.
    
    Returns the resolved URL or None if no application form was found.
    """
    if not url:
        return None
    
    # If it's already an ATS URL, return it directly
    if is_ats_url(url):
        return url
    
    # Skip file:// URLs (test forms)
    if url.startswith("file://"):
        return url
    
    # Try HTTP-based resolution first (lightweight, no browser needed)
    resolved = _resolve_via_http(url)
    if resolved:
        return resolved
    
    # If a Playwright page is provided, try browser-based resolution
    if page:
        resolved = _resolve_via_browser(url, page)
        if resolved:
            return resolved
    
    return None


def _resolve_via_http(url: str) -> str | None:
    """Fetch the page HTML and look for ATS links."""
    try:
        import httpx
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = httpx.get(url, headers=headers, timeout=15.0, follow_redirects=True)
        
        if response.status_code != 200:
            return None
        
        html = response.text
        
        # Extract all href values
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        
        # Look for ATS URLs in the hrefs
        for href in hrefs:
            # Resolve relative URLs
            if href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            
            if is_ats_url(href):
                print(f"  [URL Resolver] Found ATS apply link: {href}")
                return href
        
        # Also check for apply-related anchors with external links
        apply_patterns = [
            r'href=["\']([^"\']*(?:apply|career|job|position)[^"\']*)["\']',
        ]
        
        for pattern in apply_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith("http") and is_ats_url(match):
                    print(f"  [URL Resolver] Found apply link via pattern: {match}")
                    return match
        
    except Exception as e:
        print(f"  [URL Resolver] HTTP resolution failed: {e}")
    
    return None


def _resolve_via_browser(url: str, page) -> str | None:
    """Use the provided Playwright page to navigate and find apply links."""
    try:
        page.goto(url, timeout=20000)
        page.wait_for_load_state("load")
        
        # Look for Apply buttons/links
        apply_selectors = [
            "a:has-text('Apply')",
            "a:has-text('Apply Now')",
            "a:has-text('Apply for this job')",
            "a[href*='greenhouse']",
            "a[href*='lever']",
            "a[href*='workable']",
            "a[href*='ashby']",
            "a[href*='bamboo']",
            "a[href*='jobvite']",
            "a[href*='icims']",
        ]
        
        for selector in apply_selectors:
            try:
                loc = page.locator(selector)
                count = loc.count()
                for idx in range(count):
                    el = loc.nth(idx)
                    if el.is_visible():
                        href = el.get_attribute("href")
                        if href and href.startswith("http"):
                            if is_ats_url(href):
                                print(f"  [URL Resolver] Browser found ATS link: {href}")
                                return href
                            # Even non-ATS apply links are valid targets
                            if any(kw in href.lower() for kw in ["apply", "career", "job"]):
                                print(f"  [URL Resolver] Browser found apply link: {href}")
                                return href
            except Exception:
                pass
        
        # If we found form elements on the current page, the URL itself is the form
        form_elements = page.query_selector_all("input[type='text'], input[type='email'], textarea")
        visible_inputs = sum(1 for el in form_elements if el.is_visible())
        if visible_inputs >= 2:
            print(f"  [URL Resolver] Current page has {visible_inputs} visible form fields — using current URL")
            return url
        
    except Exception as e:
        print(f"  [URL Resolver] Browser resolution failed: {e}")
    
    return None


if __name__ == "__main__":
    # Quick test
    test_urls = [
        "https://boards.greenhouse.io/test/jobs/123",
        "https://jobs.lever.co/company/xyz",
        "https://www.ycombinator.com/companies/test",
    ]
    for u in test_urls:
        print(f"{u} -> ATS: {is_ats_url(u)}")
