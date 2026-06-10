# 🎓 AI Career Assistant & Agent Architecture

An advanced, modular, and persistent multi-agent framework designed to assist candidates with profile exploration, ATS resume formatting, portfolio website creation, and stateful mock interview coaching with performance metrics analytics.

---

## 🏗️ Architecture & Information Flow

The system operates across 5 decoupled layers to enforce separation of concerns and semantic data access:

```text
                  +----------------------------------------------+
                  |            Routing Layer (app.py)            |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |                 Agent Layer                  |
                  |  [Profile] [Resume] [Portfolio] [Recruiter]  |
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
- **Memory Layer:** Static caching of candidate profile segments for semantic lookup (RAG), and ChromaDB persistence for mock interview sessions.
- **Agent Layer:** Decoupled behavior engines handling task evaluation, resume compilation, and coaching feedback.
- **Routing Layer:** Multi-page Streamlit web dashboard.
- **LLM Layer:** Centralized Gemini model generation and embeddings interface.

For a deeper dive into data flows and schemas, see the complete [Architecture Specification](file:///d:/temp/ai-agent-roadmap/docs/architecture.md).

---

## ✨ Core Features

*   💬 **Semantic Profile Assistant:** Real-time conversational search powered by Retrieval-Augmented Generation (RAG) which indexes and queries profile segments.
*   📄 **ATS Resume Builder:** Instantly generates chronological, single-column technical resumes designed to score high on Applicant Tracking Systems, with support for **PDF, HTML, and Markdown** downloads.
*   🌐 **Portfolio Web Designer:** Dynamically designs readable Markdown-based developer portfolios with direct downloads for Markdown and styled HTML formats.
*   🧠 **Interactive Interview Recruiter:** Conducts live mock interview sessions tailored to a chosen job role, evaluates answers against profile items (TypeScript, WebSockets, Next.js), writes constructive feedback, and saves history.
*   💼 **Career Advisor & Performance Report:** Reads persistent interview logs from ChromaDB to analyze and output a structured coaching report identifying your consistently weak areas, strong topics, and next-step roadmap.

---

## 📦 Directory Structure

```text
ai-agent-roadmap/
├── agents/             # Modular agent behavior classes
├── data/               # Ground truth profile JSON and cache index
├── docs/               # System architecture design and generated PDF/HTML reports
├── memory/             # Vector cache builders and ChromaDB database files
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
   pip install google-generativeai python-dotenv chromadb streamlit fpdf2
   ```

4. Create a `.env` file at the project root and add your Gemini API Key:
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

### 1. ATS Resume Generation (Excerpt)
```markdown
# Abiyan Ahmed
Bengaluru, Karnataka, India | +91 7019972653 | abiyanahmed777@gmail.com

## Technical Skills
- Languages: TypeScript, JavaScript
- Web Dev: Next.js, React, tRPC, Progressive Web Apps (PWA)
- Databases: Prisma, Relational Modeling
```

### 2. Recruiter Coach Evaluation
> **🤖 Question:** *How did you implement offline support in your CODTECH PWA?*  
> **💡 Feedback Summary:** Excellent! You correctly identified Service Workers and static asset caching. To improve, mention Cache First strategies and cache versioning.  
> **🏆 Suggested Model Answer:** *"To enable robust offline support, I registered a Service Worker caching static assets via a Cache First strategy, fallback loading offline routes immediately when network requests failed..."*

---

## 🌐 Cloud Deployment

- **UI Dashboard:** Deploy to [Streamlit Community Cloud](https://streamlit.io/cloud) by linking your GitHub repository and registering your `GEMINI_API_KEY` under Streamlit Secret Settings.
- **Backend / DB State:** For persistent databases across multiple users, ChromaDB can be deployed as an independent server on [Render](https://render.com) or [Railway](https://railway.app).
