import sys
import os
import json
from tools.gemini_client import model
from tools.load_profile import load_profile

def get_interview_history_safely():
    """Tries to retrieve interview history from ChromaDB, handling missing package/DB scenarios."""
    try:
        from memory.vector_store import get_all_interview_history
        return get_all_interview_history()
    except Exception as e:
        print(f"[Warning] Could not retrieve database records: {e}")
        return []

def analyze_performance(profile, history):
    """Summarizes past mock interview performance to identify strengths and weaknesses."""
    if not history:
        return (
            "You don't have any mock interview sessions recorded in database memory yet!\n"
            "Go practice with the **Interview Coach** first to generate performance logs."
        )
        
    history_context = "\n\n".join([f"--- Record {i+1} ---\n{doc}" for i, doc in enumerate(history)])
    
    prompt = f"""
You are an expert engineering manager and technical interview coach.
Analyze the candidate's profile and their historical mock interview Q&A and feedback sessions below:

Candidate Profile:
{json.dumps(profile, indent=2)}

Past Interview Performance Logs:
{history_context}

Please generate a professional, structured performance analysis outlining:
1. **Consistently Struggled / Weak Areas**: Key concepts, skills, or topics where the candidate's answers were weak or incomplete (e.g., System Design, Caching, Databases, concurrency, conflict resolution).
2. **Strong Areas**: Technical domains or skills they explained well (e.g., React, Next.js, TypeScript).
3. **Actionable Roadmap**: Clear, specific learning steps and topics they should focus on next.

Format the output in clean Markdown. Be direct, constructive, and highly professional.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def answer_general_career_query(profile, history, query):
    """Answers general career advising questions utilizing profile and interview history context."""
    history_summary = ""
    if history:
        history_summary = "Past Interview History Summary (for context):\n" + "\n\n".join(history[:5])
        
    prompt = f"""
You are a senior career advisor and technical coach.
Answer the candidate's career question based on their profile and past interview performance context:

Candidate Profile:
{json.dumps(profile, indent=2)}

{history_summary}

Candidate's Question:
"{query}"

Provide a professional, practical, and constructive response tailored to their skills and background.
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
    print("💼 AI CAREER ADVISOR & PERFORMANCE COACH")
    print("==================================================")
    print("Type 'exit' to quit.")
    print("Type 'weaknesses' to analyze your past mock interview performance.")
    print("==================================================")

    while True:
        try:
            query = input("\nAsk Career Advisor:\n> ").strip()
            if not query:
                continue
            if query.lower() == "exit":
                print("Returning to main menu...")
                break
                
            history = get_interview_history_safely()
            
            if "weak" in query.lower() or "strong" in query.lower() or query.lower() == "weaknesses" or "performance" in query.lower():
                print("\nAnalyzing past interview logs from database memory...")
                feedback = analyze_performance(profile, history)
                print("\nPerformance Summary:")
                print(feedback)
            else:
                print("\nThinking...")
                response = answer_general_career_query(profile, history, query)
                print("\nAdvisor Response:")
                print(response)
                
            print("\n" + "=" * 50)
        except (KeyboardInterrupt, EOFError):
            print("\nReturning to main menu...")
            break

if __name__ == "__main__":
    main()
