import sys
import os
import json
from tools.gemini_client import model
from tools.load_profile import load_profile

def clean_json_output(text):
    """Safely extracts raw JSON array text from model output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove markdown wrappers
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def generate_questions(profile, role):
    """Generates exactly 10 custom interview questions based on the candidate's profile."""
    prompt = f"""
You are an expert technical recruiter and interviewer.
Analyze the candidate's profile:
{json.dumps(profile, indent=2)}

Generate exactly 10 interview questions tailored for the target role: "{role}".
The questions must probe the candidate's actual projects (e.g., Collaborative Editor, AI Development Workspace), experience (e.g., CODTECH internship), and skills (Next.js, React, TypeScript, Prisma, WebSockets, PWAs). Make them realistic, technical, and personalized.

Your output must be a valid JSON array of 10 strings.
Do not include any formatting other than the JSON array itself (no markdown formatting or code block wrappers).
Example output format:
[
  "Question 1...",
  "Question 2..."
]
"""
    response = model.generate_content(prompt)
    cleaned_text = clean_json_output(response.text)
    
    try:
        questions = json.loads(cleaned_text)
        if isinstance(questions, list) and len(questions) > 0:
            return questions[:10]
    except Exception as e:
        print(f"\n[Warning] Failed to parse questions JSON. Error: {e}. Falling back to default questions.")
    
    # Fallback default questions in case model output structure fails
    return [
        f"How did you leverage TypeScript to reduce runtime errors by 25% in your AI Development Workspace?",
        f"Can you explain how your real-time synchronization engine in the Collaborative Editor guarantees data integrity using WebSockets?",
        f"What caching strategies did you implement using Service Workers to improve the CODTECH PWA performance by 30%?",
        f"How do you ensure end-to-end type safety across the client and server using the T3 stack (Next.js, React, tRPC, Prisma)?",
        f"In your HI BUN Cafe System, how did you model the relational database schema in Prisma to automate inventory tracking?",
        f"What are the benefits of using a Progressive Web App (PWA) over a native mobile app in the context of your CODTECH internship?",
        f"How do you handle conflict resolution in concurrent multi-user collaborative environments?",
        f"Why is Next.js preferred over standard React for high-traffic e-commerce platforms?",
        f"What was the most challenging technical block in your Collaborative Editor project and how did you resolve it?",
        f"Where do you see the future of AI development workspaces heading, and how does your project fit into that roadmap?"
    ]

def evaluate_answer(profile, role, question, answer):
    """Evaluates the candidate's answer and provides constructive feedback."""
    prompt = f"""
You are a senior tech lead and interview coach.
The candidate is interviewing for the role: "{role}".

Candidate Profile:
{json.dumps(profile, indent=2)}

Question Asked:
"{question}"

Candidate's Answer:
"{answer}"

Provide professional, constructive feedback on their answer. Highlight:
1. **Strengths**: What they explained well.
2. **Areas of Improvement**: What technical details, keywords, or specifics they missed or could expand on (prompt them to reference specific skills/projects from their profile like Next.js, Prisma, WebSockets, or the CODTECH internship).
3. **Suggested Model Answer**: A concise, exemplary answer that links their profile credentials perfectly to the question.

Make your feedback encouraging, punchy, and highly actionable. Output in clean Markdown formatting.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def main():
    # Force standard output to UTF-8 to prevent encoding crashes on Windows consoles
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    try:
        profile = load_profile()
    except Exception as e:
        print(f"Error loading profile: {e}")
        return

    print("==================================================")
    print("🎓 AI INTERVIEW COACH & CAREER AGENT")
    print("==================================================")
    
    role = input("Enter target role: ").strip()
    if not role:
        role = "Software Developer"
        print(f"Defaulting target role to: {role}")
        
    print(f"\nAnalyzing profile and generating 10 personalized questions for '{role}'...")
    questions = generate_questions(profile, role)
    
    print("\nInitialization complete! Type 'exit' at any point to end the session.\n")
    print("==================================================")

    for idx, question in enumerate(questions, 1):
        print(f"\n[Question {idx}/10]")
        print(f"🤖 {question}")
        
        try:
            answer = input("\nYour Answer:\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
            
        if answer.lower() == "exit":
            print("\nEnding session. Good luck with your interview preparation!")
            break
            
        print("\nAnalyzing answer and generating coach feedback...")
        feedback = evaluate_answer(profile, role, question, answer)
        
        print("\nFeedback:")
        print(feedback)
        print("\n" + "=" * 50)

    print("\nInterview coaching session finished. Keep practice, you got this!")

if __name__ == "__main__":
    main()
