import os
import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # Use realistic user agent
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    try:
        response = page.goto("https://news.ycombinator.com/jobs", wait_until="networkidle", timeout=30000)
        print("Status code:", response.status if response else "No response")
        print("Page Title:", page.title())
        content = page.content()
        print(f"Content length: {len(content)}")
        
        # Check anchors again
        anchors = page.query_selector_all(".titleline > a")
        print(f"Anchors with '.titleline > a': {len(anchors)}")
        
        if len(anchors) == 0:
            # Let's check other selectors
            all_anchors = page.query_selector_all("a")
            print(f"Total anchors: {len(all_anchors)}")
            for idx, a in enumerate(all_anchors[:20]):
                print(f"  {idx}: text='{a.inner_text().strip()}', href='{a.get_attribute('href')}'")
    except Exception as e:
        print("Error during navigation:", e)
    browser.close()
