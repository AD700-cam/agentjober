# 🎓 AI Career Assistant & Agent Architecture

An advanced, modular, and persistent multi-agent framework designed to assist candidates with profile exploration, ATS resume formatting, portfolio website creation, stateful mock interview coaching with performance metrics analytics, automated job scraping, application readiness grading, and customized resume tailoring.

---

## 🏗️ Architecture & Information Flow

The system operates across 5 decoupled layers to enforce separation of concerns and semantic data access:

```text
                  +----------------------------------------------+
                  |  Routing Layer (app.py / Background Cron)   |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |                 Agent Layer                  |
                  | [Profile] [Resume] [Coach] [Readiness] [Tailor]|
                  +----------------------------------------------+
                      |                   |                   |
                      v                   v                   v
       +----------------------+ +------------------+ +----------------------+
       |     Memory Layer     | |    LLM Layer     | |      Data Layer      |
       |   ChromaDB History   | |  Gemini Client   | |  master_profile.json |
       |   Vector Search Cache| |  Vector Embeds   | |                      |
       +----------------------+ +------------------+ +----------------------+
```

- **Data Layer:** Single source of truth containing resume/portfolio profile variables.
- **Memory Layer:** Static caching of candidate profile segments for semantic lookup (RAG), and ChromaDB persistence for mock interview sessions and crawled job posts.
- **Agent Layer:** Decoupled behavior engines handling task evaluation, resume compilation, coaching feedback, readiness metrics, and tailored resumes.
- **Routing Layer:** Multi-page Streamlit web dashboard and background daily scraping schedules.
- **LLM Layer:** Centralized Gemini model generation and embeddings interface.

For a deeper dive into data flows and schemas, see the complete [Architecture Specification](file:///d:/temp/ai-agent-roadmap/docs/architecture.md).

---

## ✨ Core Features

*   💬 **Semantic Profile Assistant:** Real-time conversational search powered by Retrieval-Augmented Generation (RAG) which indexes and queries profile segments.
*   📄 **ATS Resume Builder:** Instantly generates chronological, single-column technical resumes designed to score high on Applicant Tracking Systems, with support for **PDF, HTML, and Markdown** downloads.
*   🌐 **Portfolio Web Designer:** Dynamically designs readable Markdown-based developer portfolios with direct downloads for Markdown and styled HTML formats.
*   🧠 **Interactive Interview Recruiter:** Conducts live mock interview sessions tailored to a chosen job role, evaluates answers against profile items (TypeScript, WebSockets, Next.js), writes constructive feedback, and saves history.
*   💼 **Career Advisor & Performance Report:** Reads persistent interview logs from ChromaDB to analyze and output a structured coaching report identifying your consistently weak areas, strong topics, and next-step roadmap.
*   🔍 **Automated Daily Job Pipeline (NEW):** Leverages `apscheduler` and `playwright` to run a background crawler every morning at 8:00 AM, scraping and indexing developer roles from public job boards (Hacker News Jobs) into ChromaDB.
*   📊 **Application Readiness Score (NEW):** Calculates a combined readiness grade (0-100%) against a selected job description, detailing strengths checklists, skill gaps, and custom study guides.
*   ✨ **Resume Tailoring Agent (NEW):** Dynamically alters bullet points, skill priorities, and summary statements to align with target job requirements (preserving candidate truthfulness) with downloads in Markdown, HTML, and PDF.

---

## 📦 Directory Structure

```text
ai-agent-roadmap/
├── agents/             # Modular agent behavior classes (coaching, tailoring, readiness)
├── data/               # Ground truth profile JSON and cache index
├── docs/               # System architecture design and generated PDF/HTML reports
├── memory/             # Vector cache builders and ChromaDB database files
├── scrapers/           # Playwright job board crawler engine and JSON stores
├── scratch/            # Automated verification test suites and inspection files
├── tools/              # Shared Gemini configurations, embedders, and exporters
├── app.py              # Streamlit Web UI Entry Point
├── main.py             # CLI Terminal Entry Point
└── requirements.txt    # Project dependencies
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.10+
- A Google Gemini API Key

### Local Installation
1. Clone this repository and navigate to the folder:
   ```bash
   git clone <repository-url>
   cd ai-agent-roadmap
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. Install required libraries:
   ```bash
   pip install google-generativeai python-dotenv chromadb streamlit fpdf2 playwright apscheduler
   ```

4. Install Playwright browser binaries:
   ```bash
   playwright install chromium
   ```

5. Create a `.env` file at the project root and add your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Running the App
*   **To run the Web UI (Recommended):**
   ```bash
   streamlit run app.py
   ```
*   **To run the Terminal CLI:**
   ```bash
   python main.py
   ```

---

## 📊 Example Outputs

### 1. Application Readiness Assessment (Job Matcher)
```json
{
  "match_score": 82,
  "strengths": ["React", "TypeScript", "Next.js"],
  "gaps": ["Testing (Jest)", "CI/CD (GitHub Actions)", "AWS Fundamentals"],
  "recommendations": [
    "1. Learn Jest: write unit tests for components",
    "2. Set up GitHub Actions: automate your builds"
  ]
}
```

### 2. Resume Tailoring Agent
Outputs an ATS-optimized Markdown document:
```markdown
# Abiyan Ahmed
[Email](mailto:abiyanahmed777@gmail.com) | [GitHub](https://github.com/AD700-cam)

## Core Skills (Prioritized)
- Frontend: TypeScript, React, Next.js, WebSockets, PWAs
- Databases & Tools: Prisma, Git, GitHub

## Professional Experience
- Designed a mobile-first PWA e-commerce site, optimizing Service Workers...
```

---

## 🌐 Cloud Deployment

- **UI Dashboard:** Deploy to [Streamlit Community Cloud](https://streamlit.io/cloud) by linking your GitHub repository and registering your `GEMINI_API_KEY` under Streamlit Secret Settings. Note: Streamlit Cloud uses ephemeral environments; local ChromaDB database files will reset on container rebuilds.
- **Persistent DB State:** For persistent databases, ChromaDB can be run as an independent server hosted on cloud platforms like [Render](https://render.com) or [Railway](https://railway.app).
