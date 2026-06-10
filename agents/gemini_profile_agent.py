import json
import os
import sys
from tools.gemini_client import model
from tools.load_profile import load_profile

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

    print("=== AI Profile Agent ===")
    print("Type 'exit' to quit")

    while True:
        try:
            question = input("\nAsk: ").strip()
            if not question:
                continue
            if question.lower() == "exit":
                print("Returning to main menu...")
                break

            prompt = f"""
You are a personal career assistant.

User Profile:

{json.dumps(profile, indent=2)}

Answer this question using ONLY the profile information:

Question:
{question}
"""
            response = model.generate_content(prompt)
            print("\nAnswer:")
            print(response.text)
        except (KeyboardInterrupt, EOFError):
            print("\nReturning to main menu...")
            break

if __name__ == "__main__":
    main()