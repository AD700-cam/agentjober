import sys
import os
import json
from tools.gemini_client import model
from tools.load_profile import load_profile

def generate_portfolio(profile):
    """Generates a modern, professional developer portfolio in Markdown using Gemini."""
    prompt = f"""
You are an expert web designer and technical copywriter.
Create a beautifully structured, modern developer portfolio in Markdown format using the following profile information:

{json.dumps(profile, indent=2)}

Please structure the portfolio markdown with the following mandatory sections:
1. **Hero Section**: A catchy headline/tagline, a brief punchy introduction, and quick links to LinkedIn, GitHub, and Portfolio.
2. **About Me**: A professional, engaging narrative about the developer's background, academic path (BCA at Smt. Danamma Channabasavaiah College), and development philosophy.
3. **Skills**: A cleanly organized category-based list of programming languages, web dev frameworks, databases, and tools.
4. **Experience**: Professional roles (like internship at CODTECH) detailed with bullet points describing key contributions.
5. **Projects**: Detailed project showcase sections showing project names, descriptions, tech stacks, key features, and outcomes/impact.
6. **Contact**: A clean call-to-action for reaching out (Email, Phone, Location, Socials).

Formatting Guidelines:
- Use clean Markdown headers (`#`, `##`, `###`) to create a clear layout hierarchy.
- Make the tone modern, proactive, and developer-centric.
- Output ONLY the markdown content of the portfolio itself. Do not include any conversational preamble or outro.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def main():
    # Force standard output to UTF-8 to prevent encoding crashes on Windows consoles
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass # Standard stream reconfiguration not supported (e.g. old Python versions)
    try:
        profile = load_profile()
    except Exception as e:
        print(f"Error loading profile: {e}")
        return

    print("=== AI Portfolio Agent ===")
    print("Type 'Generate portfolio' to create your developer portfolio, or 'exit' to quit.")

    while True:
        try:
            user_input = input("\nAsk: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            # Check for portfolio generation command
            if "generate" in user_input.lower() and "portfolio" in user_input.lower():
                print("\nGenerating developer portfolio from master_profile.json...")
                portfolio_content = generate_portfolio(profile)
                
                # Save generated portfolio to docs directory
                os.makedirs("docs", exist_ok=True)
                output_path = "docs/portfolio.md"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(portfolio_content)
                
                print(f"\n[Success] Portfolio generated and saved to {output_path}!")
                print("\n--- Generated Portfolio ---")
                print(portfolio_content)
                print("---------------------------")
            else:
                print("Please type 'Generate portfolio' or 'exit'.")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
