import os
import json
import sys
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

    print("=== Personal Profile Agent ===")
    print("Type 'exit' to quit")

    while True:
        try:
            question = input("\nAsk me something about your profile: ").lower().strip()
            if not question:
                continue

            if question == "exit":
                print("Returning to main menu...")
                break

            elif "skill" in question:
                print("\nSkills:")
                for category, items in profile["skills"].items():
                    if items:
                        print(f"\n{category}:")
                        for item in items:
                            print(f"  • {item}")

            elif "project" in question:
                print("\nProjects:")
                for project in profile["projects"]:
                    print(f"\n📌 {project['project_name']}")
                    print(project["description"])

            elif "education" in question:
                for edu in profile["education"]:
                    print("\nEducation:")
                    print(f"Degree: {edu['degree']}")
                    print(f"Institution: {edu['institution']}")
                    print(f"University: {edu['university']}")
                    print(f"Graduation: {edu['end_year']}")

            elif "experience" in question or "internship" in question:
                print("\nWork Experience:")
                for exp in profile["work_experience"]:
                    print(f"\n🏢 Company: {exp['company']}")
                    print(f"💼 Role: {exp['role']}")
                    print("\nResponsibilities:")
                    for r in exp["responsibilities"]:
                        print(f"  • {r}")
                    print("\nAchievements:")
                    for a in exp["achievements"]:
                        print(f"  • {a}")

            elif "contact" in question:
                info = profile["personal_info"]
                print("\nContact Information:")
                print("Email:", info["email"])
                print("Phone:", info["phone"])
                print("Portfolio:", info["portfolio"])

            else:
                print("Sorry, I don't understand that yet.")
        except (KeyboardInterrupt, EOFError):
            print("\nReturning to main menu...")
            break

if __name__ == "__main__":
    main()