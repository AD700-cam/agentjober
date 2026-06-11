# tools/run_manual_login.py

import os
import sys
from playwright.sync_api import sync_playwright

# Ensure project root in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

STATE_PATH = os.path.join(project_root, "data", "auth_state.json")

def main():
    print("=======================================================")
    print("🔐 AI Career Assistant - Manual Login Session Manager")
    print("=======================================================")
    print("This utility launches a visible (headful) browser window")
    print("so you can log into job portals (LinkedIn, Google, etc.).")
    print("Your logged-in session will be saved to reuse on automated runs.")
    print("=======================================================\n")
    
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    
    with sync_playwright() as p:
        print("🚀 Launching headful Chromium browser...")
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Load state if it exists to preserve existing session and let you refresh it
        context_options = {
            "viewport": {"width": 1280, "height": 800},
            "locale": "en-US"
        }
        if os.path.exists(STATE_PATH) and os.path.getsize(STATE_PATH) > 0:
            print(f"🔄 Loading existing session state from {STATE_PATH} to update...")
            context_options["storage_state"] = STATE_PATH
            
        context = browser.new_context(**context_options)
        
        # Apply stealth (even in headful to avoid triggering bot detection during login)
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(context)
        except ImportError:
            pass
            
        page = context.new_page()
        
        print("\n🌐 Opening LinkedIn sign-in page...")
        try:
            page.goto("https://www.linkedin.com/login", timeout=45000)
        except Exception as e:
            print(f"⚠️ Navigation warning: {e}. Opening default page instead.")
            page.goto("https://www.google.com")
            
        print("\n👉 ACTION REQUIRED:")
        print("1. Log into your account(s) in the browser window.")
        print("2. Complete any required 2FA / MFA / CAPTCHA checks.")
        print("3. Ensure you are fully logged in and can see your feed/home page.")
        print("4. Return to this console and press Enter to save your login session.")
        
        input("\n⌨️ Press [ENTER] once you are successfully logged in to save state...")
        
        print("\n💾 Saving authenticated storage state...")
        context.storage_state(path=STATE_PATH)
        print(f"✅ Success! Session state saved successfully to: {STATE_PATH}")
        
        browser.close()
        print("\n👋 Done! You can now run the pipeline in headless mode.")

if __name__ == "__main__":
    main()
