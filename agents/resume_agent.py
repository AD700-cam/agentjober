import sys
import os
import json
from tools.gemini_client import model
from tools.load_profile import load_profile

def generate_ats_resume(profile):
    """Generates an ATS-optimized professional resume using Gemini."""
    prompt = f"""
You are an expert resume writer specializing in ATS-optimized (Applicant Tracking System) resumes for technical professionals.
Create a highly professional, ATS-friendly resume in Markdown format using the following user profile data:

{json.dumps(profile, indent=2)}

Guidelines for ATS optimization:
1. Structure the resume with standard section headings:
   - Name and Contact Information
   - Professional Summary
   - Core Skills (grouped logically, e.g., Languages, Frameworks, Tools)
   - Professional Experience
   - Projects
   - Education
2. Keep the formatting clean and chronological. Do not use tables, multiple columns, or custom formatting indicators that would trip up an ATS parser.
3. Frame bullet points under Experience and Projects focusing on actions and outcomes (e.g. "Automated inventory tracking resulting in improved sales operations").
4. Output ONLY the markdown text of the resume. Do not include any conversational intro/outro text.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def main():
    # Force standard output to UTF-8 to prevent encoding crashes on Windows consoles
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass # Standard stream reconfiguration not supported (e.g. old Python versions)
    try:
        profile = load_profile()
    except Exception as e:
        print(f"Error loading profile: {e}")
        return

    print("=== AI Resume Agent ===")
    print("Type 'Generate ATS resume' to create a resume, or 'exit' to quit.")

    while True:
        try:
            user_input = input("\nAsk: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            # Check for resume generation command
            if "generate" in user_input.lower() and "resume" in user_input.lower():
                print("\nGenerating ATS-optimized resume from master_profile.json...")
                resume_content = generate_ats_resume(profile)
                
                # Save generated resume to docs directory
                os.makedirs("docs", exist_ok=True)
                output_path = "docs/resume.md"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(resume_content)
                
                print(f"\n[Success] Professional resume generated and saved to {output_path}!")
                print("\n--- Generated Resume ---")
                print(resume_content)
                print("------------------------")
            else:
                print("Please type 'Generate ATS resume' or 'exit'.")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
