import os
import sys
from playwright.sync_api import sync_playwright

# Force UTF-8 encoding support to prevent crashes on Windows consoles when printing emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.auto_submitter_agent import AutoSubmitterAgent

# Subclass to mock Gemini responses to keep tests offline, fast, and quota-friendly
class OfflineAutoSubmitterAgent(AutoSubmitterAgent):
    def _generate_custom_answer(self, question: str) -> str:
        return f"Mock answer for: {question}"

def test_platform(page, agent, filename, platform_name):
    print(f"\n--- Testing Platform: {platform_name.upper()} ---")
    mock_form_path = os.path.join(project_root, "scratch", filename)
    mock_form_url = "file:///" + os.path.abspath(mock_form_path).replace("\\", "/")
    
    print(f"Mock Form URL: {mock_form_url}")
    
    # Run application filling & submission simulation
    for log in agent.fill_job_application(page, mock_form_url, submit=True):
        print(f"  > {log}")
        
    # Verify submission status
    success_locator = page.locator("#success")
    if success_locator.is_visible():
        success_text = success_locator.inner_text().strip()
        print(f"✅ SUCCESS! Success message found: '{success_text}'")
        return True
    else:
        print(f"❌ ERROR! Success message not visible for {platform_name.upper()}.")
        return False

def main():
    print("=== Testing New Platform Adapters (Phase 5 Expansion) ===")
    
    resume_path = os.path.join(project_root, "Resume.pdf")
    if not os.path.exists(resume_path):
        resume_path = os.path.join(project_root, "requirements.txt") # fallback text file
        
    failures = []
    
    with sync_playwright() as p:
        print("\n[Playwright] Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        agent = OfflineAutoSubmitterAgent(resume_path=resume_path)
        
        platforms = [
            ("test_linkedin.html", "linkedin"),
            ("test_ashby.html", "ashby"),
            ("test_smartrecruiters.html", "smartrecruiters"),
            ("test_icims.html", "icims"),
            ("test_taleo.html", "taleo"),
        ]
        
        for filename, platform in platforms:
            success = test_platform(page, agent, filename, platform)
            if not success:
                failures.append(platform)
                
        browser.close()
        
    if failures:
        print(f"\n❌ Application automation FAILED for platforms: {', '.join(failures)}")
        sys.exit(1)
    else:
        print("\n🎉 All 5 platforms automated and validated successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
