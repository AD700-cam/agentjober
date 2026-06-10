import sys
from tools.gemini_client import model
from memory.manager import search

def main():
    # Force standard output to UTF-8 to prevent encoding crashes on Windows consoles
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    print("=== AI Profile Assistant (Semantic Memory Mode) ===")
    print("Type 'exit' to quit")

    while True:
        try:
            question = input("\nAsk: ").strip()
            if not question:
                continue
            if question.lower() == "exit":
                print("Returning to main menu...")
                break

            print("\nRetrieving relevant profile context from memory...")
            context = search(question, top_k=3)

            prompt = f"""
You are a personal career assistant.

Below is the semantically relevant context retrieved from the candidate's profile:

{context}

Answer this question using ONLY the retrieved profile context above. If the answer cannot be found in the retrieved context, politely state that you do not have that information.

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