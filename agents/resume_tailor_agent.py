import json
from tools.gemini_client import model

def tailor_resume(profile: dict, job_details: str) -> str:
    """Generates an ATS-optimized, custom-tailored technical resume matching the job description."""
    prompt = f"""
You are an expert resume writer and technical recruiter.
Your goal is to tailor the candidate's resume to match the following target job description as closely as possible, ensuring the resume is highly optimized for applicant tracking systems (ATS).

Candidate Profile Data:
{json.dumps(profile, indent=2)}

Target Job Description:
{job_details}

Guidelines for Tailoring:
1. **Professional Summary**: Rewrite the summary statement to directly align with the requirements of the job. Emphasize matching years of experience and domain expertise.
2. **Skills Sorting**: Re-order and prioritize skills in the skills section to highlight the technologies most requested by the job description first.
3. **Tailored Bullet Points**: Adapt and rephrase the bullet points in the Work Experience and Projects sections to highlight outcomes, metrics, or technologies that align with the job description. Do NOT fabricate any experiences, jobs, or technologies that are not present in the candidate's profile; instead, re-frame existing achievements to highlight relevant aspects.
4. **Standard Headings**: Keep standard single-column sections (Name and Contact Info, Professional Summary, Core Skills, Professional Experience, Projects, Education) without graphical tables or columns.
5. **Output**: Return ONLY the raw Markdown text of the tailored resume. Do not include conversational introductory or concluding text.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[Resume Tailor Error] Failed to generate tailored resume: {e}")
        # Safe fallback: return standard resume generation
        from agents.resume_agent import generate_ats_resume
        return generate_ats_resume(profile)
