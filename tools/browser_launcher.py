# tools/browser_launcher.py

import os
import random
from playwright.sync_api import Playwright, Browser, BrowserContext, Page

DEFAULT_STATE_PATH = "data/auth_state.json"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def launch_browser_with_context(
    playwright: Playwright,
    headless: bool = True,
    state_path: str = DEFAULT_STATE_PATH
) -> tuple[Browser, BrowserContext, Page]:
    """
    Launches Chromium with realistic user-agent, randomized viewport,
    stealth mode applied, and optionally loads persistent auth state.
    """
    # Select a random user agent
    user_agent = random.choice(USER_AGENTS)
    
    # Randomized viewport (typical laptop sizes)
    width = random.randint(1280, 1440)
    height = random.randint(800, 950)
    
    # Chromium launch args to evade simple flags
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    )
    
    context_options = {
        "user_agent": user_agent,
        "viewport": {"width": width, "height": height},
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "accept_downloads": True
    }
    
    # Load storage state if it exists
    if os.path.exists(state_path) and os.path.getsize(state_path) > 0:
        print(f"[Browser Launcher] Loading persistent session state from: {state_path}")
        context_options["storage_state"] = state_path
    else:
        print("[Browser Launcher] No persistent session state found. Launching fresh context.")
        
    context = browser.new_context(**context_options)
    
    # Apply playwright-stealth
    try:
        from playwright_stealth import stealth_sync
        stealth_sync(context)
        print("[Browser Launcher] Stealth features enabled successfully.")
    except ImportError:
        print("[Browser Launcher] Warning: playwright-stealth not installed. Running without stealth.")
        
    page = context.new_page()
    page.set_default_timeout(30000)
    
    return browser, context, page
