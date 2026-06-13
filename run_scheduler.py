# run_scheduler.py

import os
import sys
import time
import subprocess
import argparse
from datetime import datetime

# Ensure project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.notifier import send_daily_summary

# Force UTF-8 encoding support
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def run_job():
    print(f"\n🔔 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Triggering scheduled job run...")
    python_exe = sys.executable
    script_path = os.path.join(project_root, "run_pipeline.py")
    
    # Build command arguments
    args = [python_exe, script_path, "--min-score", "40", "--max-apply", "8"]
    
    # Propagate submission flag if scheduler was started with it or via env variable
    if "--submit" in sys.argv or os.getenv("AUTO_SUBMIT", "false").lower() == "true":
        args.append("--submit")
        
    try:
        result = subprocess.run(args, check=True)
        print(f"🔔 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled job completed successfully (Exit Code: {result.returncode}).")
    except subprocess.CalledProcessError as e:
        print(f"❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled job execution failed: {e}")
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error starting scheduled job: {e}")

def main():
    parser = argparse.ArgumentParser(description="Cross-platform APscheduler Daemon for daily pipeline runs")
    parser.add_argument("--submit", action="store_true", help="Enable actual submission of job forms in scheduled runs")
    parser.add_argument("--now", action="store_true", help="Run the pipeline once immediately at startup, then enter scheduler loop")
    
    args = parser.parse_args()
    
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except ImportError:
        print("❌ Error: 'apscheduler' library is not installed in current Python environment.")
        print("Please install it: pip install apscheduler")
        sys.exit(1)
        
    print("\n=======================================================")
    print("⏰ Starting AI Career Assistant Background Daemon Scheduler")
    print(f"Startup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Schedule:     Daily at 09:00 AM")
    print(f"Mode:         Submission={args.submit}")
    print("=======================================================\n")
    
    if args.now or os.getenv("RUN_ON_STARTUP", "false").lower() == "true":
        print("🚀 Executing initial startup run (requested)...")
        run_job()
        
    scheduler = BlockingScheduler()
    # Schedule to run daily at 9:00 AM
    scheduler.add_job(run_job, 'cron', hour=9, minute=0, id='daily_career_pipeline')
    
    print("⚡ Scheduler started. Waiting in background... (Press Ctrl+C to terminate)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Scheduler terminated. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
