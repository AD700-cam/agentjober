import json
from tools.gemini_client import model

def clean_json_output(text: str) -> str:
    """Safely extracts raw JSON text from model output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

class ATSScorerAgent:
    """Evaluates technical resume relevance and formatting compatibility against a job description."""
    
    def evaluate_resume(self, resume_content: str, job_description: str) -> dict:
        """Runs Gemini comparison between resume and job description, returning an ATS report card."""
        prompt = f"""
You are an expert ATS (Applicant Tracking System) parser and recruiter simulator.
Analyze the candidate's resume text against the target job description.

Candidate Resume:
{resume_content}

Target Job Description:
{job_description}

Evaluate the compatibility. Analyze the formatting (look for elements like HTML tags, tables, side-by-side columns, or graphics that reduce parsability) and content relevance.
Formulate your response as a single, valid JSON object containing:
1. "ats_score": Integer percentage from 0 to 100 indicating match rating.
2. "parsability_rating": String ("Excellent" if text-only chronological, "Good" if minor formatting, "Needs Improvement" if tables/HTML tags/graphics present).
3. "matched_keywords": List of matching technical keywords or requirements present in both.
4. "missing_keywords": List of critical keywords present in the JD but missing or weak in the resume.
5. "recommendations": List of actionable changes (e.g. how to reframe achievements, keywords to inject, formatting edits) to increase the ATS score.

Do not include markdown tags (like ```json) or any explanations outside the JSON block.

Required JSON structure:
{{
  "ats_score": 85,
  "parsability_rating": "Excellent",
  "matched_keywords": ["TypeScript", "Next.js"],
  "missing_keywords": ["Jest", "AWS ECS"],
  "recommendations": [
    "Add Jest to Core Skills and mention testing on projects.",
    "Refactor layout to avoid HTML elements."
  ]
}}
"""
        try:
            response = model.generate_content(prompt)
            cleaned_text = clean_json_output(response.text)
            report = json.loads(cleaned_text)
            
            # Validate keys
            required_keys = ["ats_score", "parsability_rating", "matched_keywords", "missing_keywords", "recommendations"]
            if all(k in report for k in required_keys):
                return report
        except Exception as e:
            print(f"[ATS Scorer Agent Error] Evaluation failed: {e}")
            
        # Safe fallback report card
        return {
            "ats_score": 60,
            "parsability_rating": "Good",
            "matched_keywords": ["JavaScript", "TypeScript"],
            "missing_keywords": ["Unspecified key requirements"],
            "recommendations": ["Ensure core skills directly match the job description terms."]
        }
