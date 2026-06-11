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

def main():
    print("=== Testing Auto-Submitter Agent (Phase 4) ===")
    
    # 1. Paths configuration
    mock_form_path = os.path.join(project_root, "scratch", "test_form.html")
    mock_form_url = "file:///" + os.path.abspath(mock_form_path).replace("\\", "/")
    
    # Use the generated Resume.pdf or a dummy pdf if not found
    resume_path = os.path.join(project_root, "Resume.pdf")
    if not os.path.exists(resume_path):
        resume_path = os.path.join(project_root, "demo", "sample_jobs.json") # fall back to any existing file for testing
        print(f"[Test] Using fallback mock file for upload: {resume_path}")
        
    print(f"Mock Form URL: {mock_form_url}")
    print(f"Resume Path: {resume_path}")
    
    # 2. Launch Playwright
    with sync_playwright() as p:
        print("\n[Playwright] Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # 3. Instantiate Agent
        agent = AutoSubmitterAgent(resume_path=resume_path)
        
        # 4. Run fill and submit pipeline
        print("\n[Agent] Initiating auto-apply automation...")
        for log in agent.fill_job_application(page, mock_form_url, submit=True):
            print(f"  > {log}")
            
        # 5. Assertions and Verification
        print("\n[Verification] Validating page submission state...")
        
        # Check if success message is visible
        success_msg_locator = page.locator("#success-msg")
        is_visible = success_msg_locator.is_visible()
        
        if is_visible:
            success_text = success_msg_locator.inner_text().strip()
            print(f"🎉 Success! Success message found: '{success_text}'")
            
            # Check fields are empty / form is hidden
            form_visible = page.locator("#app-form").is_visible()
            if not form_visible:
                print("✅ Verified: Form has been successfully submitted and hidden.")
                print("\n=== Auto-Submitter test completed successfully! ===")
                browser.close()
                sys.exit(0)
            else:
                print("❌ Error: Form is still visible after submission.")
        else:
            print("❌ Error: Success message was not displayed. Auto-submission failed.")
            
        browser.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
