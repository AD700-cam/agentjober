# run_pipeline.py

import os
import sys
import argparse
import json
import re
import time
from datetime import datetime

# Ensure project root is in python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Force UTF-8 encoding support to prevent crashes on Windows consoles when printing emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from tools.load_profile import load_profile
from tools.export_utils import markdown_to_pdf
from scrapers.job_scraper import scrape_jobs
from memory.vector_store import search_matching_jobs, save_scraped_job
from agents.readiness_agent import evaluate_application_readiness
from agents.resume_tailor_agent import tailor_resume
from agents.cover_letter_agent import CoverLetterAgent
from agents.ats_scorer_agent import ATSScorerAgent
from agents.auto_submitter_agent import AutoSubmitterAgent
from tools.browser_launcher import launch_browser_with_context
from tools.notifier import send_notification

def main():
    parser = argparse.ArgumentParser(description="End-to-end Job Search, Tailoring, and Application Pipeline")
    parser.add_argument("--submit", action="store_true", help="Enable actual submission of job forms (Simulation mode by default)")
    parser.add_argument("--min-score", type=int, default=60, help="Minimum readiness score threshold to trigger applications (default: 60)")
    parser.add_argument("--max-jobs", type=int, default=15, help="Maximum number of job listings to crawl (default: 15)")
    parser.add_argument("--profile-path", type=str, default="data/master_profile.json", help="Path to candidate profile JSON")
    
    args = parser.parse_args()
    
    print("\n=======================================================")
    print("🚀 Starting AI Career Assistant Automated Pipeline")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modes: Submission={args.submit} | MinScore={args.min_score} | MaxJobs={args.max_jobs}")
    print("=======================================================\n")
    
    send_notification(f"Pipeline execution initiated (Submit={args.submit}, MinScore={args.min_score}, MaxJobs={args.max_jobs})", "info")
    
    # 1. Load profile
    try:
        profile = load_profile(args.profile_path)
        skills_dict = profile.get("skills", {})
        skills_list = []
        if isinstance(skills_dict, dict):
            for cat, items in skills_dict.items():
                if items:
                    skills_list.extend(items)
        else:
            skills_list = skills_dict
        candidate_name = profile.get("personal_info", {}).get("name", "Candidate")
        print(f"✅ Loaded master profile for '{candidate_name}' (Skills: {', '.join(skills_list[:6])}...)")
    except Exception as e:
        print(f"❌ Failed to load profile: {e}")
        sys.exit(1)
        
    # 2. Run background jobs crawler
    print("\n🔍 Fetching latest job listings from Hacker News...")
    try:
        crawled_jobs = scrape_jobs(max_jobs=args.max_jobs)
        print(f"✅ Scraped and indexed {len(crawled_jobs)} listings.")
    except Exception as e:
        print(f"⚠️ Job crawling encountered an error: {e}. Attempting matching on existing database.")
        
    # 3. Read crawled jobs database backup to retrieve job URLs
    crawled_db = []
    json_path = os.path.join(project_root, "scrapers", "job_store.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                crawled_db = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load job URL mappings: {e}")

    # 4. Search matching jobs using vector storage
    print("\n🧠 Querying semantic database for relevant job listings...")
    matches = search_matching_jobs(skills_list, n_results=args.max_jobs)
    if not matches:
        print("ℹ️ No matched jobs found in database. Ending pipeline.")
        sys.exit(0)
        
    print(f"📋 Found {len(matches)} potential job matches.")
    
    # 5. Load application history to prevent duplicates
    applied_urls = set()
    history_path = os.path.join(project_root, "data", "application_history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                for record in history:
                    url = record.get("url")
                    if url:
                        applied_urls.add(url.strip().lower())
        except Exception:
            pass
            
    # 6. Process matched listings
    applied_count = 0
    skipped_count = 0
    
    for idx, m in enumerate(matches, 1):
        meta = m.get("metadata", {})
        title = meta.get("title", "Unknown Title")
        company = meta.get("company", "Unknown Company")
        desc = m.get("document", "")
        job_id = m.get("id")
        
        # Resolve original URL
        job_url = ""
        for j in crawled_db:
            if j.get("title") == title and j.get("company") == company:
                job_url = j.get("url", "")
                break
                
        # Skip if already applied
        if job_url and job_url.strip().lower() in applied_urls:
            print(f"\n[{idx}/{len(matches)}] Skip: '{title}' at '{company}' (already processed).")
            skipped_count += 1
            continue
            
        print(f"\n[{idx}/{len(matches)}] Processing match: '{title}' at '{company}'")
        if job_url:
            print(f"    URL: {job_url}")
            
        # 6a. Evaluate readiness
        evaluation = evaluate_application_readiness(profile, desc)
        readiness_score = evaluation.get("match_score", 50)
        print(f"    Readiness Score: {readiness_score}%")
        
        # Skip if below threshold
        if readiness_score < args.min_score:
            print(f"    Score {readiness_score}% below target threshold {args.min_score}%. Skipping.")
            skipped_count += 1
            continue
            
        # 6b. Tailor Resume & Cover Letter
        print("    Refining candidate documentation for this listing...")
        tailored_resume = tailor_resume(profile, desc)
        
        # Create unique directory for tailored outputs
        safe_company = re.sub(r'[\s/\\?%*:|"<>]', '_', company.lower())
        out_dir = os.path.join(project_root, "data", "tailored_applications", f"{safe_company}_{job_id}")
        os.makedirs(out_dir, exist_ok=True)
        
        # Save tailored resume markdown
        resume_md_path = os.path.join(out_dir, "resume_tailored.md")
        with open(resume_md_path, "w", encoding="utf-8") as f:
            f.write(tailored_resume)
            
        # Compile resume PDF
        resume_pdf_path = os.path.join(out_dir, "resume_tailored.pdf")
        try:
            markdown_to_pdf(tailored_resume, resume_pdf_path)
            print(f"    ✅ Tailored resume saved: {resume_pdf_path}")
        except Exception as pdf_err:
            print(f"    ⚠️ PDF compilation failed: {pdf_err}. Falling back to default Resume.pdf.")
            resume_pdf_path = "Resume.pdf"
            
        # Generate custom cover letter
        cl_agent = CoverLetterAgent()
        cover_letter = cl_agent.generate_cover_letter(profile, desc)
        
        cover_md_path = os.path.join(out_dir, "cover_letter.md")
        with open(cover_md_path, "w", encoding="utf-8") as f:
            f.write(cover_letter)
        print(f"    ✅ Tailored cover letter saved: {cover_md_path}")
        
        # Evaluate ATS score
        ats_scorer = ATSScorerAgent()
        ats_report = ats_scorer.evaluate_resume(tailored_resume, desc)
        ats_score = ats_report.get("ats_score", 50)
        print(f"    ATS Compatibility: {ats_score}% (Parsability: {ats_report.get('parsability_rating', 'Good')})")
        
        # 6c. Execute auto-apply agent
        print("    Running form automation browser agent...")
        from playwright.sync_api import sync_playwright
        
        # If no real URL exists, default to test form sandbox to prevent crash
        target_url = job_url if job_url else f"file:///{os.path.abspath('scratch/test_form.html').replace('\\', '/')}"
        
        apply_metadata = {
            "company": company,
            "title": title,
            "readiness_score": readiness_score,
            "ats_score": ats_score,
            "job_id": job_id
        }
        
        submit_mode = True if args.submit else "review"
        
        try:
            with sync_playwright() as p:
                browser, context, page = launch_browser_with_context(p, headless=True)
                
                # Instantiate AutoSubmitter with the custom tailored PDF resume path
                agent = AutoSubmitterAgent(profile_path=args.profile_path, resume_path=resume_pdf_path)
                
                for log_entry in agent.fill_job_application(page, target_url, submit=submit_mode, metadata=apply_metadata):
                    print(f"      > {log_entry}")
                    
                browser.close()
                print("    ✅ Browser automation workflow complete.")
                applied_count += 1
                
                if submit_mode == True:
                    send_notification(f"Submitted application for **{company}** - *{title}* (Readiness: {readiness_score}%, ATS: {ats_score}%)", "success")
                else:
                    send_notification(f"Application for **{company}** - *{title}* filled and placed in Review Queue (Readiness: {readiness_score}%, ATS: {ats_score}%)", "review")
                
        except Exception as apply_err:
            error_msg = f"Automation failed for **{company}** - *{title}*: {apply_err}"
            print(f"    ❌ {error_msg}")
            send_notification(error_msg, "error")
            
    summary_msg = f"Automated Pipeline Execution Complete.\nProcessed: {applied_count} applied/queued | {skipped_count} skipped/filtered"
    print(f"\n=======================================================")
    print(f"🏁 {summary_msg}")
    print("=======================================================\n")
    send_notification(summary_msg, "success" if applied_count > 0 else "info")

if __name__ == "__main__":
    main()
