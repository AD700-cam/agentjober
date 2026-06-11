# src/llm/resume_generator.py

import os
import sys
import json

# Add project root to sys.path to allow importing tools modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.llm.gemini_client import generate_resume
from tools.load_profile import load_profile
from tools.export_utils import markdown_to_pdf

def build_tailoring_prompt(profile: dict, job_description: str) -> str:
    """Constructs a high-quality ATS-optimization and tailoring prompt."""
    return f"""
You are an expert resume writer and technical recruiter specializing in ATS-optimized (Applicant Tracking System) resumes.
Your goal is to tailor the candidate's profile data to match the target job description as closely as possible, ensuring the resume is highly optimized for ATS parsers.

Candidate Profile Data:
{json.dumps(profile, indent=2)}

Target Job Description:
{job_description}

Guidelines for Tailoring:
1. **Formatting**: Create a clean, single-column chronological resume in raw Markdown format. Do not use tables, side-by-side columns, custom graphics, or inline HTML styling.
2. **Professional Summary**: Rewrite the summary statement to align directly with the target job requirements. Emphasize matching years of experience, domain expertise, and core strengths.
3. **Core Skills**: Re-order and prioritize the technologies in the skills section to highlight the languages, frameworks, and tools most requested by the job description first.
4. **Professional Experience**: Adapt and rephrase the bullet points under the Experience section to highlight achievements, metrics, outcomes, or technologies that align with the job description. Do NOT fabricate any experiences, jobs, or technologies that are not present in the candidate's profile; instead, re-frame existing achievements to highlight relevant aspects (e.g. actions and outcomes).
5. **Projects**: Align project descriptions and outcomes to emphasize matching skills (e.g., WebSockets, TypeScript, etc.) without altering the actual project scope or truthfulness.
6. **Structure**: Organize the resume with standard, clear headings:
   - Name and Contact Information
   - Professional Summary
   - Core Skills (grouped logically)
   - Professional Experience
   - Projects
   - Education
7. **Output**: Return ONLY the raw Markdown text of the resume. Do not include any conversational introduction, explanation, markdown block wraps (like ```markdown ... ```), or outro.
"""

def main():
    # Force standard output to UTF-8 to prevent encoding crashes on Windows consoles
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    print("=== AI Resume Prompt Pipeline (Phase 3) ===")

    # Load master profile
    try:
        profile = load_profile()
        print(f"[Success] Loaded master profile for: {profile.get('personal_info', {}).get('name', 'Candidate')}")
    except Exception as e:
        print(f"[Error] Failed to load profile: {e}")
        sys.exit(1)

    # Get job description text
    job_description = ""
    if len(sys.argv) > 1:
        # Check if argument is a file path
        arg_path = sys.argv[1]
        if os.path.exists(arg_path):
            try:
                with open(arg_path, "r", encoding="utf-8") as f:
                    job_description = f.read().strip()
                print(f"[Info] Loaded job description from file: {arg_path}")
            except Exception as e:
                print(f"[Error] Failed to read job description file: {e}")
                sys.exit(1)
        else:
            # Otherwise treat argument as the job description text itself
            job_description = arg_path.strip()
            print("[Info] Loaded job description from command-line argument.")
    
    # If no job description is loaded, check for a default file or prompt the user
    if not job_description:
        default_jd_path = os.path.join(project_root, "data", "job_description.txt")
        if os.path.exists(default_jd_path):
            try:
                with open(default_jd_path, "r", encoding="utf-8") as f:
                    job_description = f.read().strip()
                print(f"[Info] Loaded job description from default file: data/job_description.txt")
            except Exception as e:
                pass
        
    if not job_description:
        print("\nEnter or paste the Job Description below (Press Ctrl+Z/Ctrl+D and Enter to submit on a new line):")
        try:
            lines = sys.stdin.read()
            job_description = lines.strip()
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(1)

    if not job_description:
        print("[Error] Job description is empty. Cannot tailor resume.")
        sys.exit(1)

    print("\n[Tailoring] Generating ATS-Optimized resume via Gemini 2.5 Pro...")
    
    # Construct tailoring prompt
    prompt = build_tailoring_prompt(profile, job_description)
    
    # Call Gemini client
    try:
        tailored_resume_md = generate_resume(prompt).strip()
        # Strip code fences if returned by model
        if tailored_resume_md.startswith("```markdown"):
            tailored_resume_md = tailored_resume_md[11:]
        elif tailored_resume_md.startswith("```"):
            tailored_resume_md = tailored_resume_md[3:]
        if tailored_resume_md.endswith("```"):
            tailored_resume_md = tailored_resume_md[:-3]
        tailored_resume_md = tailored_resume_md.strip()
    except Exception as e:
        print(f"[Error] Failed to generate tailored resume from Gemini: {e}")
        sys.exit(1)

    # Save to Markdown
    md_output_path = os.path.join(project_root, "ATS-Optimized Resume.md")
    try:
        with open(md_output_path, "w", encoding="utf-8") as f:
            f.write(tailored_resume_md)
        print(f"[Success] Saved Markdown resume to: {md_output_path}")
    except Exception as e:
        print(f"[Error] Failed to save Markdown resume: {e}")
        sys.exit(1)

    # Save to PDF
    pdf_output_path = os.path.join(project_root, "Resume.pdf")
    try:
        markdown_to_pdf(tailored_resume_md, pdf_output_path)
        print(f"[Success] Saved PDF resume to: {pdf_output_path}")
    except Exception as e:
        print(f"[Error] Failed to save PDF resume: {e}")
        sys.exit(1)

    print("\n--- Pipeline Complete! ATS-Optimized tailored resume generated successfully. ---")

if __name__ == "__main__":
    main()
