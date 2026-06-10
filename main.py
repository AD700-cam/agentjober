import sys
from agents import gemini_profile_agent
from agents import resume_agent
from agents import portfolio_agent
from agents import interview_agent

def main():
    # Force standard output to UTF-8 to prevent encoding crashes on Windows consoles
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    while True:
        print("\n=== AI Career Assistant ===")
        print("1. Profile Assistant")
        print("2. Resume Generator")
        print("3. Portfolio Generator")
        print("4. Interview Coach")
        print("5. Exit")
        
        try:
            choice = input("\nChoose:\n> ").strip()
            if not choice:
                continue
            
            if choice == "1":
                print("\n" + "=" * 50)
                gemini_profile_agent.main()
                print("=" * 50)
            elif choice == "2":
                print("\n" + "=" * 50)
                resume_agent.main()
                print("=" * 50)
            elif choice == "3":
                print("\n" + "=" * 50)
                portfolio_agent.main()
                print("=" * 50)
            elif choice == "4":
                print("\n" + "=" * 50)
                interview_agent.main()
                print("=" * 50)
            elif choice == "5" or choice.lower() == "exit":
                print("\nThank you for using AI Career Assistant. Goodbye!")
                break
            else:
                print("\n[Error] Invalid choice. Please choose a number from 1 to 5.")
        except (KeyboardInterrupt, EOFError):
            print("\n\nThank you for using AI Career Assistant. Goodbye!")
            break

if __name__ == "__main__":
    main()
