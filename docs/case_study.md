# Case Study: Building an AI-Powered Career Intelligence Platform

## Problem

Job seekers face a fragmented workflow: they manually search job boards, copy-paste descriptions into ChatGPT for resume advice, run mock interviews with no persistent memory, and have no systematic way to track which skills they're weak in over time. Existing tools are either expensive SaaS products or shallow wrappers around a single LLM call.

**Key pain points identified:**
- No unified system connecting job discovery → readiness assessment → resume customization → interview preparation
- Mock interview feedback is stateless — users can't track improvement over time
- Resume customization is manual and time-consuming per application
- Job board scraping requires technical setup most candidates don't have

---

## Architecture

I designed a **5-layer modular agent architecture** that separates concerns cleanly:

```
┌─────────────────────────────────────────────────────────┐
│                   Routing Layer                         │
│              Streamlit UI + APScheduler Cron            │
├─────────────────────────────────────────────────────────┤
│                    Agent Layer                          │
│  Profile │ Resume │ Coach │ Readiness │ Tailor │ Advisor│
├──────────┬──────────────────┬───────────────────────────┤
│ Memory   │    LLM Layer     │      Data Layer           │
│ ChromaDB │  Gemini + Embeds │   master_profile.json     │
└──────────┴──────────────────┴───────────────────────────┘
```

**Why this design:**
- **Decoupled agents** can be tested, extended, or replaced independently
- **ChromaDB vector store** enables semantic search across interview history and job listings — not just keyword matching
- **Background scheduler** automates the scraping pipeline so the job database stays fresh without user intervention
- **Profile-as-JSON** serves as a single source of truth that all agents reference, avoiding data drift

---

## Technical Decisions

### 1. RAG over Fine-Tuning
I chose Retrieval-Augmented Generation (RAG) instead of fine-tuning a model on the candidate's data. **Rationale:** The profile data changes frequently (new projects, skills, experiences). RAG lets me update the vector index in seconds without retraining. The system chunks the profile into semantic segments, embeds them using Gemini's embedding model, and retrieves the top-3 relevant chunks per query using cosine similarity.

### 2. ChromaDB for Persistent Memory
Mock interview Q&A sessions are stored as embedded documents in ChromaDB. This means when a user asks "What are my weak areas?", the Career Advisor agent performs a semantic query across all past interview logs — not just the current session. This creates **longitudinal performance tracking**, which is the key differentiator from stateless chatbot wrappers.

### 3. Playwright over API-based Scraping
I chose Playwright (headless browser automation) over HTTP scraping because modern job boards render content dynamically via JavaScript. Playwright handles this natively. I targeted Hacker News Jobs specifically because it's crawler-friendly and doesn't violate any terms of service. A realistic User-Agent header was required to avoid HTTP 429 rate limiting.

### 4. APScheduler for Automated Refresh
Instead of requiring users to manually click "scrape," I integrated `apscheduler`'s `BackgroundScheduler` directly into the Streamlit process. It runs a cron job at 8:00 AM daily, refreshing the job database automatically. This was chosen over system-level cron or Celery because it requires zero external infrastructure — important for a portfolio project that needs to run anywhere.

### 5. Structured JSON Agent Outputs
All evaluation agents (Readiness, Job Matcher) are prompted to return **strict JSON** with validated keys. This enables the UI to render structured components (progress bars, badge lists, numbered recommendations) rather than unparseable freeform text. A fallback response is always returned if parsing fails.

---

## Challenges

### Challenge 1: Embedding Model Integration
ChromaDB's default embedding function downloads a 400MB+ transformer model on first use. This was unacceptable for a portfolio project. **Solution:** I bypassed ChromaDB's built-in embeddings entirely and passed pre-computed vectors from Gemini's `gemini-embedding-001` model directly to `.add()` and `.query()` calls.

### Challenge 2: Rate Limiting on Hacker News
The Playwright scraper initially received HTTP 429 ("Sorry") responses. **Solution:** Creating a browser context with a realistic Chrome User-Agent header resolved this immediately. Sub-pages for job detail text are also opened through the same context to share cookies and session state.

### Challenge 3: Streamlit Stateful Interactions
Streamlit reruns the entire script on every interaction. Interview state (current question index, feedback history) and job evaluations would be lost. **Solution:** All stateful data is stored in `st.session_state` dictionaries, keyed by job ID or question index, persisting across reruns.

### Challenge 4: Windows Encoding Crashes
Gemini responses containing emoji or Unicode characters crashed the Windows console. **Solution:** `sys.stdout.reconfigure(encoding='utf-8')` is applied at the top of every entry point, with a try/except for older Python versions.

---

## Results

| Metric | Value |
|--------|-------|
| Total agents implemented | 7 (Profile, Resume, Portfolio, Coach, Advisor, Readiness, Tailor) |
| Resume tailoring output | 4,017 characters of customized, ATS-optimized content |
| Readiness evaluation | Identifies strengths, gaps, and generates numbered study plans |
| ChromaDB collections | 3 (interview_history, career_memory, job_listings) |
| Job scraping throughput | 30 listings parsed per crawl cycle |
| Automated pipeline | Daily 8:00 AM cron via APScheduler |
| Export formats | Markdown, HTML, PDF for resumes and reports |
| Vector embedding model | Gemini `gemini-embedding-001` (768 dimensions) |
| Persistent interview memory | Longitudinal performance analysis across sessions |

---

## Future Improvements

1. **Multi-source Job Aggregation:** Extend the scraper to pull from multiple public boards (GitHub Jobs API, RemoteOK, public company career pages) and deduplicate listings.
2. **Interview Trend Analytics:** Visualize performance over time with charts showing improvement trajectories per skill category.
3. **Cover Letter Generation Agent:** Use the tailoring pipeline architecture to also generate targeted cover letters.
4. **Deployed Live Demo:** Host on Streamlit Community Cloud with a remote ChromaDB server for persistent data across sessions.
5. **Demo Video Recording:** Create a 2–3 minute walkthrough demonstrating the full workflow from job scraping to tailored resume download.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend/UI | Streamlit |
| LLM | Google Gemini 3.5 Flash |
| Embeddings | Gemini Embedding 001 (768-dim) |
| Vector Database | ChromaDB (persistent, local) |
| Web Scraping | Playwright (headless Chromium) |
| Scheduling | APScheduler (BackgroundScheduler) |
| PDF Generation | fpdf2 |
| Language | Python 3.14 |

---

*Author: Abiyan Ahmed | [GitHub](https://github.com/AD700-cam) | [Portfolio](https://abxn.dev)*
