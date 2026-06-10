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
from agents.readiness_agent import evaluate_application_readiness
from agents.resume_tailor_agent import tailor_resume

def main():
    print("--- Testing Readiness Assessment & Resume Tailoring Pipeline ---")
    
    # 1. Load candidate profile
    profile = load_profile()
    
    # 2. Define a target job description requiring testing and cloud tools (gaps)
    mock_job = """
    Job Title: Senior React & TypeScript Developer
    Company: ScaleTech
    Location: Bengaluru / Remote
    Description: We are seeking a Senior Developer proficient in React, Next.js, and TypeScript.
    Critical requirements:
    - Experience setting up testing suites using Jest and React Testing Library.
    - Familiarity with CI/CD deployment pipelines (GitHub Actions, Docker).
    - Deploying and maintaining backend APIs on AWS infrastructure (ECS, Amplify, RDS).
    - Experience with real-time architectures (WebSockets).
    """
    
    print("\n[Step 1] Evaluating Application Readiness...")
    readiness_result = evaluate_application_readiness(profile, mock_job)
    print("\nReadiness Analysis Output:")
    print(json.dumps(readiness_result, indent=2))
    
    # Assert keys exist
    for key in ["match_score", "strengths", "gaps", "recommendations"]:
        if key not in readiness_result:
            print(f"Error: Missing key '{key}' in readiness output.")
            sys.exit(1)
            
    print(f"\nMatch score: {readiness_result['match_score']}%")
    print(f"Identified Strengths: {readiness_result['strengths']}")
    print(f"Identified Gaps: {readiness_result['gaps']}")
    print(f"Recommendations: {len(readiness_result['recommendations'])} items generated.")
    
    print("\n[Step 2] Tailoring Resume...")
    tailored_resume = tailor_resume(profile, mock_job)
    print(f"\nResume Tailoring completed. Output length: {len(tailored_resume)} characters.")
    
    if len(tailored_resume) > 100:
        print("\nTailored Resume Snippet (First 500 characters):")
        print(tailored_resume[:500])
        print("\nPipeline test completed successfully!")
    else:
        print("\nError: Tailored resume is too short or failed to generate.")
        sys.exit(1)

if __name__ == "__main__":
    main()
