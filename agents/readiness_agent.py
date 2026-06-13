import os
import json
import re
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


def _keyword_fallback_score(profile: dict, job_doc: str) -> dict:
    """
    Fast, free keyword-overlap scorer used when Gemini API is unavailable.
    Computes a readiness score based on how many of the candidate's skills 
    appear in the job description text.
    """
    # Gather all candidate skills into a flat lowercase set
    skills_dict = profile.get("skills", {})
    all_skills = []
    if isinstance(skills_dict, dict):
        for cat, items in skills_dict.items():
            if isinstance(items, list):
                all_skills.extend([s.lower().strip() for s in items if s])
    elif isinstance(skills_dict, list):
        all_skills = [s.lower().strip() for s in skills_dict if s]
    
    # Add project technologies
    for proj in profile.get("projects", []):
        for tech in proj.get("technologies", []):
            if tech:
                all_skills.append(tech.lower().strip())
    
    # Deduplicate
    all_skills = list(set(all_skills))
    
    if not all_skills:
        return {
            "match_score": 30,
            "strengths": [],
            "gaps": ["Could not extract skills from profile"],
            "recommendations": ["Update your master_profile.json with your skills"]
        }
    
    job_text = job_doc.lower()
    
    # Count matches
    matched_skills = []
    missing_skills = []
    for skill in all_skills:
        # Use word boundary matching for short terms
        if len(skill) <= 3:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, job_text):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)
        else:
            if skill in job_text:
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)
    
    # Calculate score: percentage of skills that match, scaled to 0-100
    if len(all_skills) > 0:
        raw_score = (len(matched_skills) / len(all_skills)) * 100
    else:
        raw_score = 30
    
    # Boost score if key skills match (React, TypeScript, JavaScript, Next.js)
    key_skills = ["react", "typescript", "javascript", "next.js", "nextjs", "node", "nodejs"]
    key_matches = [s for s in matched_skills if s in key_skills]
    if key_matches:
        raw_score = min(100, raw_score + len(key_matches) * 8)
    
    score = int(min(100, max(10, raw_score)))
    
    return {
        "match_score": score,
        "strengths": [s.title() for s in matched_skills[:10]],
        "gaps": [s.title() for s in missing_skills[:6]],
        "recommendations": [f"Strengthen your {s.title()} skills" for s in missing_skills[:3]]
    }


def evaluate_application_readiness(profile: dict, job_doc: str) -> dict:
    """Uses Gemini to evaluate a candidate's readiness for a job, returning structured strengths, gaps, and recommendations.
    Falls back to keyword-based scoring if Gemini is unavailable."""
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
        print(f"[Readiness Agent Warning] Gemini API unavailable: {e}")
        print(f"[Readiness Agent] Using keyword-based fallback scorer...")
    
    # Keyword-based fallback instead of blind 50%
    return _keyword_fallback_score(profile, job_doc)
