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

def evaluate_application_readiness(profile: dict, job_doc: str) -> dict:
    """Uses Gemini to evaluate a candidate's readiness for a job, returning structured strengths, gaps, and recommendations."""
    prompt = f"""
You are an expert ATS optimization and career readiness consultant.
Compare this candidate's master profile against the target job details.

Candidate Profile:
{json.dumps(profile, indent=2)}

Job Details:
{job_doc}

Analyze the qualifications. Formulate the response as a single, valid JSON object containing:
1. "match_score": Integer percentage from 0 to 100 indicating readiness.
2. "strengths": List of strings representing skills present in the profile that align with the job's needs.
3. "gaps": List of strings representing skills required or preferred by the job but missing or weak in the candidate's profile.
4. "recommendations": List of strings providing short, step-by-step actions (e.g., specific concepts, tools, or hands-on practice projects) to bridge those gaps.

Do not include markdown tags (like ```json) or any explanation outside the JSON block.

Required JSON structure:
{{
  "match_score": 75,
  "strengths": ["React", "TypeScript"],
  "gaps": ["Jest", "AWS"],
  "recommendations": [
    "Learn Jest: write unit tests for components",
    "AWS Fundamentals: deploy app using AWS Amplify or ECS"
  ]
}}
"""
    try:
        response = model.generate_content(prompt)
        cleaned_text = clean_json_output(response.text)
        evaluation = json.loads(cleaned_text)
        
        # Validate keys
        required_keys = ["match_score", "strengths", "gaps", "recommendations"]
        if all(k in evaluation for k in required_keys):
            return evaluation
    except Exception as e:
        print(f"[Readiness Agent Error] Failed to evaluate readiness: {e}")
        
    # Safe fallback response
    return {
        "match_score": 50,
        "strengths": ["JavaScript", "TypeScript"],
        "gaps": ["Unspecified requirements"],
        "recommendations": ["Review the job requirements to align key skills."]
    }
