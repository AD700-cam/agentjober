import os
import json
import sys
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

def evaluate_job_match(profile: dict, job_doc: str) -> dict:
    """Uses Gemini to evaluate a candidate profile against a job description, returning a structured JSON match review."""
    prompt = f"""
You are an expert technical interviewer and recruiter.
Analyze how well this candidate matches the following job listing.

Candidate Profile:
{json.dumps(profile, indent=2)}

Job Listing Details:
{job_doc}

Evaluate the fit and respond ONLY with a valid JSON object matching this structure.
Do not include any Markdown wrapping (no ```json code blocks) or introductory/concluding text outside the JSON object.

Required JSON structure:
{{
  "match_score": 85,
  "overlapping_skills": ["TypeScript", "React", "Next.js"],
  "skill_gaps": ["TailwindCSS", "AWS Cloud Deployments"],
  "study_plan": "### Study Plan\\n1. **Learn TailwindCSS**: [Provide brief steps]\\n2. **AWS Cloud**: [Provide brief steps]"
}}
"""
    try:
        response = model.generate_content(prompt)
        cleaned_text = clean_json_output(response.text)
        evaluation = json.loads(cleaned_text)
        
        # Validate keys
        if "match_score" in evaluation and "overlapping_skills" in evaluation and "skill_gaps" in evaluation and "study_plan" in evaluation:
            return evaluation
    except Exception as e:
        print(f"[Job Matcher Error] Failed to evaluate job match: {e}")
        
    # Safe fallback response in case model returns malformed JSON
    return {
        "match_score": 50,
        "overlapping_skills": ["JavaScript", "TypeScript"],
        "skill_gaps": ["Unknown Core Requirements"],
        "study_plan": "Please review the job details directly. Focus on checking matching frameworks in your profile."
    }
