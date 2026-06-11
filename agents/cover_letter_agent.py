import json
from tools.gemini_client import model

class CoverLetterAgent:
    """Generates customized, professionally styled cover letters matching the target job description."""
    
    def generate_cover_letter(self, profile: dict, job_description: str) -> str:
        """Constructs a cover letter based on candidate achievements and job requirements."""
        personal_info = profile.get("personal_info", {})
        candidate_name = personal_info.get("name", "Candidate")
        
        prompt = f"""
You are an expert executive resume writer and career coach.
Create a highly professional and tailored Cover Letter in Markdown format based on the candidate's profile and the target job description.

Candidate Profile:
{json.dumps(profile, indent=2)}

Target Job Description:
{job_description}

Guidelines:
1. **Header**: Include the candidate's name, email, phone, location, and links (LinkedIn/GitHub/Portfolio) in a clean, professional header layout.
2. **Salutation**: Address the Hiring Manager professionally (e.g., "Dear Hiring Team at [Company Name]," or "Dear Hiring Manager,").
3. **Opening Paragraph**: State the specific position being applied for, express genuine enthusiasm for the company, and mention 2-3 core skills (e.g., TypeScript, Next.js) that make the candidate a perfect match.
4. **Body Paragraphs**: Focus on 1-2 real achievements from the profile (e.g. engineering PWAs, real-time WebSocket sync engine, strict type-safe modular architectures) and connect them directly to the needs of the job description. Do NOT fabricate any accomplishments, roles, or skills.
5. **Closing Paragraph**: Reiterate interest, suggest a call or interview, thank them for their time.
6. **Sign-off**: End with a formal sign-off (e.g., "Sincerely, [Name]").
7. **Output**: Return ONLY the raw Markdown text of the cover letter. Do not include markdown block wrappers (like ```markdown ... ```) or conversational intro/outro text.
"""
        try:
            response = model.generate_content(prompt)
            letter = response.text.strip()
            
            # Strip code fences if returned
            if letter.startswith("```markdown"):
                letter = letter[11:]
            elif letter.startswith("```"):
                letter = letter[3:]
            if letter.endswith("```"):
                letter = letter[:-3]
                
            return letter.strip()
        except Exception as e:
            print(f"[Cover Letter Agent Error] Failed to generate cover letter: {e}")
            return f"""# Cover Letter for {candidate_name}

Dear Hiring Team,

I am writing to express my strong interest in the open position. With my background in software development and experience in TypeScript, React, and Next.js, I am confident in my ability to contribute value to your engineering team.

I look forward to discussing my qualifications with you in an interview.

Sincerely,
{candidate_name}
"""
