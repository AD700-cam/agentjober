import os
import sys
import json

# Force UTF-8 encoding support
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.load_profile import load_profile
from agents.job_matcher_agent import evaluate_job_match

def main():
    print("--- Testing Job Matcher Agent ---")
    
    # Load profile
    profile = load_profile()
    
    # Define a mock job description
    mock_job = """
    Job Title: Full-Stack Engineer (React & TypeScript)
    Company: TechInnovate
    Location: Remote
    Description: We are looking for a Full-Stack Developer experienced in React, Next.js, and TypeScript.
    You will build modern web applications, design clean database schemas with Prisma, and deploy to AWS.
    Experience with TailwindCSS and real-time WebSockets is a plus.
    """
    
    print("Evaluating match against mock job description...")
    evaluation = evaluate_job_match(profile, mock_job)
    
    print("\nResult:")
    print(json.dumps(evaluation, indent=2))
    
    if "match_score" in evaluation:
        print("\nSuccess! Match evaluation completed.")
    else:
        print("\nFailure: Unexpected keys in evaluation response.")

if __name__ == "__main__":
    main()
