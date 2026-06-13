# run_pipeline.py
# Main orchestrator: scrapes jobs from multiple free sources, matches against profile,
# tailors resume, and auto-applies via browser automation.

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
from tools.url_resolver import resolve_application_url, is_ats_url
from memory.vector_store import search_matching_jobs, save_scraped_job
from agents.readiness_agent import evaluate_application_readiness
from agents.resume_tailor_agent import tailor_resume
from agents.cover_letter_agent import CoverLetterAgent
from agents.ats_scorer_agent import ATSScorerAgent
from agents.auto_submitter_agent import AutoSubmitterAgent
from tools.browser_launcher import launch_browser_with_context
from tools.notifier import send_notification


def scrape_all_sources(max_jobs: int = 20) -> list[dict]:
    """Aggregates jobs from all free sources: RemoteOK, Jobicy, and Hacker News."""
    all_jobs = []
    
    # Source 1: RemoteOK (free JSON API — best for remote dev roles)
    try:
        from scrapers.remoteok_scraper import scrape_remoteok
        print("\n📡 [Source 1/3] Scraping RemoteOK...")
        remoteok_jobs = scrape_remoteok(max_jobs=max_jobs)
        all_jobs.extend(remoteok_jobs)
        print(f"  ✅ RemoteOK: {len(remoteok_jobs)} relevant jobs")
    except Exception as e:
        print(f"  ⚠️ RemoteOK scraper failed: {e}")
    
    # Source 2: Jobicy (free API — remote-only job board)
    try:
        from scrapers.jobicy_scraper import scrape_jobicy
        print("\n📡 [Source 2/3] Scraping Jobicy...")
        jobicy_jobs = scrape_jobicy(max_jobs=max_jobs)
        all_jobs.extend(jobicy_jobs)
        print(f"  ✅ Jobicy: {len(jobicy_jobs)} relevant jobs")
    except Exception as e:
        print(f"  ⚠️ Jobicy scraper failed: {e}")
    
    # Source 3: Hacker News Jobs (existing scraper)
    try:
        from scrapers.job_scraper import scrape_jobs
        print("\n📡 [Source 3/3] Scraping Hacker News Jobs...")
        hn_jobs = scrape_jobs(max_jobs=min(max_jobs, 10))
        # Tag HN jobs
        for j in hn_jobs:
            j["source"] = "hackernews"
        all_jobs.extend(hn_jobs)
        print(f"  ✅ Hacker News: {len(hn_jobs)} jobs")
    except Exception as e:
        print(f"  ⚠️ Hacker News scraper failed: {e}")
    
    print(f"\n📊 Total jobs scraped from all sources: {len(all_jobs)}")
    
    # Save combined job store
    combined_path = os.path.join(project_root, "scrapers", "job_store.json")
    try:
        with open(combined_path, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, indent=2)
    except Exception:
        pass
    
    return all_jobs


def main():
    parser = argparse.ArgumentParser(description="End-to-end Job Search, Tailoring, and Application Pipeline")
    parser.add_argument("--submit", action="store_true", help="Enable actual submission of job forms (Simulation mode by default)")
    parser.add_argument("--min-score", type=int, default=40, help="Minimum readiness score threshold to trigger applications (default: 40)")
    parser.add_argument("--max-jobs", type=int, default=20, help="Maximum number of job listings to crawl per source (default: 20)")
    parser.add_argument("--max-apply", type=int, default=8, help="Maximum number of applications to submit per run (default: 8)")
    parser.add_argument("--profile-path", type=str, default="data/master_profile.json", help="Path to candidate profile JSON")
    
    args = parser.parse_args()
    
    print("\n=======================================================")
    print("🚀 Starting AI Career Assistant Automated Pipeline")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modes: Submission={args.submit} | MinScore={args.min_score} | MaxJobs={args.max_jobs} | MaxApply={args.max_apply}")
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
        
    # 2. Scrape jobs from ALL free sources (not just HN anymore)
    print("\n🔍 Fetching latest job listings from multiple free sources...")
    all_scraped = scrape_all_sources(max_jobs=args.max_jobs)
    
    if not all_scraped:
        print("⚠️ No jobs scraped from any source. Attempting matching on existing database only.")
    
    # 3. Build a lookup map of scraped jobs by title+company for URL resolution
    crawled_db = all_scraped if all_scraped else []
    # Also load any previously saved jobs
    json_path = os.path.join(project_root, "scrapers", "job_store.json")
    if not crawled_db and os.path.exists(json_path):
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
        send_notification("Pipeline ended: No matching jobs found in database.", "info")
        sys.exit(0)
        
    print(f"📋 Found {len(matches)} potential job matches from vector store.")
    
    # 5. Load application history to prevent duplicates
    applied_urls = set()
    applied_titles = set()  # Also track by title+company to avoid duplicates without URL
    history_path = os.path.join(project_root, "data", "application_history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                for record in history:
                    url = record.get("url")
                    if url:
                        applied_urls.add(url.strip().lower())
                    # Track title+company combo too
                    key = f"{record.get('company', '').lower()}|{record.get('title', '').lower()}"
                    if key != "|":
                        applied_titles.add(key)
        except Exception:
            pass
            
    # 6. Process matched listings
    applied_count = 0
    skipped_count = 0
    run_report = []
    
    for idx, m in enumerate(matches, 1):
        # Stop if we've reached the max apply limit
        if applied_count >= args.max_apply:
            print(f"\n🛑 Reached max apply limit ({args.max_apply}). Stopping.")
            break
        
        # Introduce rate-limiting delay between jobs to prevent API quota issues (transient 429)
        if idx > 1:
            print("\n⏳ Sleeping 8 seconds between job listings to respect API rate limits...")
            time.sleep(8)
            
        meta = m.get("metadata", {})
        title = meta.get("title", "Unknown Title")
        company = meta.get("company", "Unknown Company")
        desc = m.get("document", "")
        job_id = m.get("id")
        
        # Resolve original URL from scraped database
        job_url = ""
        for j in crawled_db:
            if j.get("title") == title and j.get("company") == company:
                job_url = j.get("url", "")
                break
        
        # Also try partial matching if exact match fails
        if not job_url:
            for j in crawled_db:
                if (j.get("company", "").lower() == company.lower() or
                    j.get("title", "").lower() == title.lower()):
                    job_url = j.get("url", "")
                    break
                    
        # Skip if already applied (by URL or title+company)
        title_key = f"{company.lower()}|{title.lower()}"
        if (job_url and job_url.strip().lower() in applied_urls) or title_key in applied_titles:
            print(f"\n[{idx}/{len(matches)}] Skip: '{title}' at '{company}' (already processed).")
            skipped_count += 1
            run_report.append({
                "company": company,
                "title": title,
                "status": "Skipped ⏭️",
                "reason": "Already processed in a previous execution"
            })
            continue
            
        # Skip file:// URLs (test forms) in production
        if job_url and job_url.startswith("file://"):
            print(f"\n[{idx}/{len(matches)}] Skip: '{title}' at '{company}' (test form URL).")
            skipped_count += 1
            continue
            
        print(f"\n[{idx}/{len(matches)}] Processing match: '{title}' at '{company}'")
        if job_url:
            print(f"    URL: {job_url}")
        
        # 6a. Resolve the actual application form URL
        actual_apply_url = None
        if job_url:
            print("    🔗 Resolving application form URL...")
            actual_apply_url = resolve_application_url(job_url)
            if actual_apply_url:
                print(f"    ✅ Resolved apply URL: {actual_apply_url}")
            else:
                # Use the original URL as fallback — the AutoSubmitter will try to find Apply buttons
                actual_apply_url = job_url
                print(f"    ℹ️ Using original listing URL (will try to find Apply button)")
        
        if not actual_apply_url:
            print(f"    ⚠️ No URL available for this job. Skipping.")
            skipped_count += 1
            run_report.append({
                "company": company,
                "title": title,
                "status": "Skipped 🔗",
                "reason": "No application URL available"
            })
            continue
            
        # 6b. Evaluate readiness
        evaluation = evaluate_application_readiness(profile, desc)
        readiness_score = evaluation.get("match_score", 50)
        print(f"    Readiness Score: {readiness_score}%")
        
        # Skip if below threshold
        if readiness_score < args.min_score:
            print(f"    Score {readiness_score}% below target threshold {args.min_score}%. Skipping.")
            skipped_count += 1
            run_report.append({
                "company": company,
                "title": title,
                "status": "Filtered 📉",
                "reason": f"Readiness score ({readiness_score}%) below threshold ({args.min_score}%)"
            })
            continue
            
        # 6c. Tailor Resume & Cover Letter
        print("    ✂️ Tailoring resume for ATS optimization...")
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
        
        # 6d. Execute auto-apply agent
        print("    🤖 Running form automation browser agent...")
        from playwright.sync_api import sync_playwright
        
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
                
                for log_entry in agent.fill_job_application(page, actual_apply_url, submit=submit_mode, metadata=apply_metadata):
                    print(f"      > {log_entry}")
                    
                browser.close()
                print("    ✅ Browser automation workflow complete.")
                applied_count += 1
                
                if submit_mode == True:
                    status_label = "Submitted ✅"
                    reason_str = "Form submitted live to job board"
                    send_notification(f"Submitted application for **{company}** - *{title}* (Readiness: {readiness_score}%, ATS: {ats_score}%)", "success")
                else:
                    status_label = "Pending Review ⏳"
                    reason_str = "Form filled and placed in HITL Review Queue"
                    send_notification(f"Application for **{company}** - *{title}* filled and placed in Review Queue (Readiness: {readiness_score}%, ATS: {ats_score}%)", "review")
                
                run_report.append({
                    "company": company,
                    "title": title,
                    "status": status_label,
                    "reason": reason_str,
                    "readiness": readiness_score,
                    "ats": ats_score
                })
                
        except Exception as apply_err:
            error_msg = f"Automation failed for **{company}** - *{title}*: {apply_err}"
            print(f"    ❌ {error_msg}")
            send_notification(error_msg, "error")
            run_report.append({
                "company": company,
                "title": title,
                "status": "Failed ❌",
                "reason": str(apply_err),
                "readiness": readiness_score,
                "ats": ats_score
            })
            
    summary_msg = f"Automated Pipeline Execution Complete.\nProcessed: {applied_count} applied/queued | {skipped_count} skipped/filtered"
    print(f"\n=======================================================")
    print(f"🏁 {summary_msg}")
    print("=======================================================\n")
    
    # Compile detailed report for Telegram
    report_lines = [
        f"**Daily Execution Report**",
        f"Date: *{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        f"Mode: **{'Live Submission' if args.submit else 'Simulation / Review'}**",
        f"",
        f"**Summary:**",
        f"• Total Processed: {applied_count + skipped_count}",
        f"• Applied/Queued: {applied_count}",
        f"• Skipped/Filtered: {skipped_count}",
        f"",
        f"**Processed Listings Details:**"
    ]
    
    for r_idx, r in enumerate(run_report, 1):
        line = f"{r_idx}. **{r['company']}** - *{r['title']}*\n"
        line += f"   • Status: {r['status']}\n"
        if "readiness" in r and "ats" in r:
            line += f"   • Scores: Readiness {r['readiness']}% | ATS {r['ats']}%\n"
        line += f"   • Details: {r['reason']}"
        report_lines.append(line)
        
    full_report = "\n".join(report_lines)
    
    # Telegram character limit is 4096, truncate safely if needed
    if len(full_report) > 4000:
        full_report = full_report[:3950] + "\n\n*... (Report truncated due to length)*"
        
    send_notification(full_report, "success" if applied_count > 0 else "info")

if __name__ == "__main__":
    main()
