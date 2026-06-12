import os
import json
import tempfile
import streamlit as st

# Force UTF-8 encoding support
import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Ensure project root is in PYTHONPATH
import os
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import utilities
from tools.gemini_client import model
from tools.load_profile import load_profile
from tools.export_utils import markdown_to_html, markdown_to_pdf
from memory.manager import search, build_index
from memory.vector_store import search_matching_jobs, save_scraped_job
from agents.resume_agent import generate_ats_resume
from agents.portfolio_agent import generate_portfolio
from agents.interview_agent import generate_questions, evaluate_answer
from agents.career_advisor_agent import analyze_performance, answer_general_career_query, get_interview_history_safely

# Set Streamlit page config
st.set_page_config(
    page_title="AI Career Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look & Feel (Fast & Good Looking)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #1d4ed8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 12px;
    }
    h2, h3, h4, h5, h6, [data-testid="stHeader"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 700 !important;
    }
    
    /* Modern Dashboard Cards */
    .modern-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .modern-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    }
    
    /* Sidebar styling overrides */
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Metric Value styling */
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 34px !important;
    }
    
    /* Tab Styling */
    button[data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 600 !important;
    }
    
    /* Premium button styles */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.45) !important;
    }
    
    /* Secondary Action Button overrides */
    div.stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f8fafc !important;
        box-shadow: none !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Textarea & inputs visual enhancements */
    textarea, input[type="text"] {
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background-color: rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    textarea:focus, input[type="text"]:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* Slide-up Fade Animations (Premium Facelift) */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .element-container, .stMarkdown, .modern-card, [data-testid="stMetricValue"] {
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* Sidebar list item hover highlights */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        padding: 8px 12px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
        margin-bottom: 5px !important;
        border: 1px solid transparent !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(3px) !important;
    }

    /* Glassmorphic/HSL Table Styling */
    table {
        border-collapse: collapse !important;
        width: 100% !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin: 15px 0 !important;
    }
    th {
        background-color: rgba(59, 130, 246, 0.1) !important;
        color: #60a5fa !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        border-bottom: 2px solid rgba(59, 130, 246, 0.2) !important;
        padding: 12px !important;
        text-align: left !important;
    }
    td {
        padding: 12px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        background-color: rgba(255, 255, 255, 0.01) !important;
        color: #e2e8f0 !important;
    }
    tr:hover td {
        background-color: rgba(255, 255, 255, 0.03) !important;
    }

    /* Premium Alert Box Customization */
    [data-testid="stAlert"] {
        border-radius: 8px !important;
        background-color: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        backdrop-filter: blur(8px) !important;
    }
</style>
""", unsafe_allow_html=True)

# Cached profile loader for speed optimization
@st.cache_data
def get_cached_profile():
    return load_profile()

# Load profile data
try:
    profile = get_cached_profile()
except Exception as e:
    st.error(f"Failed to load master profile: {e}")
    st.stop()

# Auto-prime memory index on start
build_index()

# Initialize background daily scheduler
@st.cache_resource
def start_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        
        def run_pipeline_job():
            import subprocess
            import sys
            import os
            python_path = sys.executable
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_pipeline.py")
            print("[Scheduler] Triggering scheduled daily pipeline run...")
            
            # Pass submission flag if AUTO_SUBMIT env variable is set to true
            args = [python_path, script_path]
            if os.getenv("AUTO_SUBMIT", "false").lower() == "true":
                args.append("--submit")
                
            subprocess.Popen(args)
            
        scheduler = BackgroundScheduler()
        # Schedule the full pipeline to run daily at 9:00 AM
        scheduler.add_job(run_pipeline_job, "cron", hour=9, minute=0, id="daily_pipeline")
        
        # Trigger pipeline execution immediately on startup if requested
        if os.getenv("RUN_ON_STARTUP", "false").lower() == "true":
            print("[Scheduler] RUN_ON_STARTUP is enabled. Triggering immediate scheduled job run...")
            run_pipeline_job()
            
        scheduler.start()
        print("[Scheduler] Started background daily pipeline scheduler at 9:00 AM.")
        return scheduler
    except Exception as e:
        print(f"[Scheduler] Failed to start background scheduler: {e}")
        return None

scheduler = start_scheduler()

# Send startup notification to verify notification channel setup
try:
    from tools.notifier import send_notification
    send_notification("Dashboard service initialized and listening in the cloud.", "success")
except Exception as e:
    print(f"[Notifier Error] Could not send startup notification: {e}")

# App title and sidebar navigation
st.sidebar.title("🎓 AI Career Assistant")
st.sidebar.markdown("Navigate through your AI agents:")

page = st.sidebar.radio(
    "Choose Agent:",
    ["Profile Assistant", "Resume Generator", "Portfolio Generator", "Interview Coach", "Career Advisor", "Job Matcher", "HITL Review Queue", "Application Analytics"]
)

st.sidebar.divider()
st.sidebar.markdown(f"**Candidate:** {profile.get('personal_info', {}).get('name', 'N/A')}")
st.sidebar.markdown(f"**Email:** {profile.get('personal_info', {}).get('email', 'N/A')}")
st.sidebar.markdown(f"**Location:** {profile.get('personal_info', {}).get('location', 'N/A')}")

# ==================================================
# PAGE 1: PROFILE ASSISTANT
# ==================================================
if page == "Profile Assistant":
    st.title("💬 Profile Assistant")
    st.markdown("Ask the Profile Assistant any question regarding Abiyan's technical skills, experience, projects, or education. It queries relevant segments from his local vector store memory.")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    if user_query := st.chat_input("e.g., What web frameworks does he know? Tell me about his CODTECH internship."):
        # Display user message
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        # Generate response using semantic lookup
        with st.spinner("Searching profile memory..."):
            context = search(user_query, top_k=3)
            prompt = f"""
You are a personal career assistant.
Below is the semantically relevant context retrieved from the candidate's profile:

{context}

Answer this question using ONLY the retrieved profile context above. If the answer cannot be found in the retrieved context, politely state that you do not have that information.

Question:
{user_query}
"""
            try:
                response = model.generate_content(prompt)
                ans = response.text.strip()
            except Exception as e:
                ans = f"Error generating answer: {e}"

        # Display assistant response
        with st.chat_message("assistant"):
            st.write(ans)
        st.session_state.chat_history.append({"role": "assistant", "content": ans})

# ==================================================
# PAGE 2: RESUME GENERATOR
# ==================================================
elif page == "Resume Generator":
    st.title("📄 ATS Resume Generator")
    st.markdown("Generate a highly professional, single-column technical resume optimized to pass Applicant Tracking Systems (ATS).")

    if "ats_resume" not in st.session_state:
        st.session_state.ats_resume = None

    if st.button("Generate Resume", type="primary"):
        with st.spinner("Compiling profile and writing resume..."):
            st.session_state.ats_resume = generate_ats_resume(profile)
            
    if st.session_state.ats_resume:
        st.success("Resume generated successfully!")
        
        # Action Buttons
        col1, col2, col3 = st.columns(3)
        
        # 1. Download Markdown
        col1.download_button(
            label="Download Markdown (.md)",
            data=st.session_state.ats_resume,
            file_name="resume.md",
            mime="text/markdown"
        )
        
        # 2. Download HTML
        html_content = markdown_to_html(st.session_state.ats_resume)
        col2.download_button(
            label="Download HTML (.html)",
            data=html_content,
            file_name="resume.html",
            mime="text/html"
        )
        
        # 3. Download PDF
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                markdown_to_pdf(st.session_state.ats_resume, tmp.name)
                with open(tmp.name, "rb") as f:
                    pdf_data = f.read()
            col3.download_button(
                label="Download PDF (.pdf)",
                data=pdf_data,
                file_name="resume.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            col3.error(f"PDF creation failed: {e}")

        # Render preview in box
        st.divider()
        st.subheader("Resume Preview")
        st.markdown(st.session_state.ats_resume)

# ==================================================
# PAGE 3: PORTFOLIO GENERATOR
# ==================================================
elif page == "Portfolio Generator":
    st.title("🌐 Portfolio Generator")
    st.markdown("Create a modern, readable web portfolio showcasing personal details, skills, experiences, and project impact.")

    if "portfolio_md" not in st.session_state:
        st.session_state.portfolio_md = None

    if st.button("Generate Portfolio Layout", type="primary"):
        with st.spinner("Designing portfolio..."):
            st.session_state.portfolio_md = generate_portfolio(profile)

    if st.session_state.portfolio_md:
        st.success("Portfolio generated successfully!")
        
        col1, col2 = st.columns(2)
        
        # 1. Download Markdown
        col1.download_button(
            label="Download Markdown (.md)",
            data=st.session_state.portfolio_md,
            file_name="portfolio.md",
            mime="text/markdown"
        )
        
        # 2. Download HTML
        html_content = markdown_to_html(st.session_state.portfolio_md)
        col2.download_button(
            label="Download HTML (.html)",
            data=html_content,
            file_name="portfolio.html",
            mime="text/html"
        )

        st.divider()
        st.subheader("Portfolio Preview")
        st.markdown(st.session_state.portfolio_md)

# ==================================================
# PAGE 4: INTERVIEW COACH
# ==================================================
elif page == "Interview Coach":
    st.title("🧠 Interactive Interview Coach")
    st.markdown("Practice your technical mock interviews. Select a target role to generate 10 customized questions. Your responses are recorded persistently in database memory.")

    # Initialize state variables
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    if "role" not in st.session_state:
        st.session_state.role = ""
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "answered" not in st.session_state:
        st.session_state.answered = False

    if not st.session_state.interview_started:
        role_input = st.text_input("Enter target job role (e.g. Frontend Developer, Full-Stack Engineer)", "Frontend Developer")
        if st.button("Start Mock Interview", type="primary"):
            with st.spinner("Analyzing profile and crafting questions..."):
                st.session_state.questions = generate_questions(profile, role_input)
                st.session_state.role = role_input
                st.session_state.q_idx = 0
                st.session_state.interview_started = True
                st.session_state.feedback = None
                st.session_state.answered = False
                st.rerun()
    else:
        st.info(f"Target Role: **{st.session_state.role}**")
        st.subheader(f"Question {st.session_state.q_idx + 1} of 10")
        current_question = st.session_state.questions[st.session_state.q_idx]
        st.write(f"🤖 **{current_question}**")

        # Answer entry
        ans_input = st.text_area("Your Answer:", key=f"ans_q_{st.session_state.q_idx}")
        
        # Action columns
        col1, col2 = st.columns([1, 4])
        
        if col1.button("Submit Answer", type="primary", disabled=st.session_state.answered or not ans_input):
            with st.spinner("Evaluating response..."):
                fback = evaluate_answer(profile, st.session_state.role, current_question, ans_input)
                st.session_state.feedback = fback
                st.session_state.answered = True
                
                # Save to database memory
                try:
                    from memory.vector_store import save_interview_qa
                    save_interview_qa(st.session_state.role, current_question, ans_input, fback)
                except Exception as e:
                    st.warning(f"Database saving failed: {e}")
                    
                st.rerun()

        if st.session_state.answered:
            st.divider()
            st.subheader("Coach Feedback")
            st.markdown(st.session_state.feedback)
            
            if st.button("Next Question →"):
                if st.session_state.q_idx < 9:
                    st.session_state.q_idx += 1
                    st.session_state.answered = False
                    st.session_state.feedback = None
                else:
                    st.session_state.interview_started = False
                    st.success("🎉 You have completed all 10 questions! Check options in the Career Advisor to analyze your performance.")
                st.rerun()

        if st.button("Cancel Interview"):
            st.session_state.interview_started = False
            st.rerun()

# ==================================================
# PAGE 5: CAREER ADVISOR
# ==================================================
elif page == "Career Advisor":
    st.title("💼 AI Career Advisor & Performance Coach")
    st.markdown("Ask career strategy questions, check required skills, or retrieve your past mock interview history from persistent vector database memory to analyze weaknesses.")

    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("Performance Analytics")
        st.write("Generate a detailed coaching report highlighting consistent technical weaknesses and strong topics based on past interview logs.")
        
        if st.button("Analyze Weak & Strong Areas", type="primary"):
            with st.spinner("Retrieving database logs and evaluating..."):
                history = get_interview_history_safely()
                analysis = analyze_performance(profile, history)
                st.session_state.advisor_analysis = analysis

        if "advisor_analysis" in st.session_state:
            # Document Exporters for the Report
            st.download_button(
                label="Download Report (.md)",
                data=st.session_state.advisor_analysis,
                file_name="performance_report.md",
                mime="text/markdown"
            )
            
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    markdown_to_pdf(st.session_state.advisor_analysis, tmp.name)
                    with open(tmp.name, "rb") as f:
                        pdf_data = f.read()
                st.download_button(
                    label="Download Report PDF (.pdf)",
                    data=pdf_data,
                    file_name="performance_report.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Report PDF export failed: {e}")

    with col1:
        st.subheader("Advisor Chat")
        
        if "advisor_chat" not in st.session_state:
            st.session_state.advisor_chat = []

        for msg in st.session_state.advisor_chat:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if advisor_query := st.chat_input("Ask career advisor (e.g. What are my weak interview areas? What skills should I learn next?)"):
            with st.chat_message("user"):
                st.write(advisor_query)
            st.session_state.advisor_chat.append({"role": "user", "content": advisor_query})

            # Check if user explicitly asked for weaknesses/performance
            with st.spinner("Evaluating background details..."):
                history = get_interview_history_safely()
                if "weak" in advisor_query.lower() or "strong" in advisor_query.lower() or "performance" in advisor_query.lower() or "weakness" in advisor_query.lower():
                    ans = analyze_performance(profile, history)
                else:
                    ans = answer_general_career_query(profile, history, advisor_query)

            with st.chat_message("assistant"):
                st.write(ans)
            st.session_state.advisor_chat.append({"role": "assistant", "content": ans})

    # Render analysis under column block if generated
    if "advisor_analysis" in st.session_state:
        st.divider()
        st.subheader("Performance Analysis Report")
        st.markdown(st.session_state.advisor_analysis)

# ==================================================
# PAGE 6: JOB MATCHER
# ==================================================
elif page == "Job Matcher":
    st.title("🎯 AI Job Matcher & Study Planner")
    st.markdown("Instantly match your candidate profile against crawled tech job listings. Discover compatibility scores, overlapping skills, skill gaps, and custom generated study roadmaps.")

    # Flatten skills for query
    skills_dict = profile.get("skills", {})
    skills_list = []
    for cat, items in skills_dict.items():
        if items:
            skills_list.extend(items)

    # Make sure session state is initialized
    if "crawled_jobs" not in st.session_state:
        st.session_state.crawled_jobs = []
        json_path = "scrapers/job_store.json"
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    st.session_state.crawled_jobs = json.load(f)
            except Exception:
                pass

    if "job_evaluations" not in st.session_state:
        st.session_state.job_evaluations = {}

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader("Job Listings")
        
        # Crawl Button
        if st.button("🔍 Crawl & Index Tech Jobs", type="secondary", use_container_width=True):
            with st.spinner("Launching Playwright crawler and fetching jobs from HN..."):
                try:
                    from scrapers.job_scraper import scrape_jobs
                    scraped = scrape_jobs(max_jobs=15)
                    st.session_state.crawled_jobs = scraped
                    if scraped:
                        st.success(f"Crawled and indexed {len(scraped)} jobs successfully!")
                        st.rerun()
                    else:
                        st.warning("No jobs found on this run. Check network connection.")
                except Exception as e:
                    st.error(f"Scraper error: {e}")

        # Search/Filter query
        search_query = st.text_input("Filter job database (empty for semantic skills-match):", "")

        # Fetch matched jobs
        with st.spinner("Searching matching jobs..."):
            if search_query:
                # If the user typed a specific query, search by that query vector
                matches = search_matching_jobs([search_query], n_results=10)
            else:
                # Semantic match based on profile skills
                # Ensure jobs are indexed if database is empty but json store isn't
                matches = search_matching_jobs(skills_list, n_results=10)
                if len(matches) == 0 and len(st.session_state.crawled_jobs) > 0:
                    for job in st.session_state.crawled_jobs:
                        try:
                            save_scraped_job(
                                title=job["title"],
                                company=job["company"],
                                location=job["location"],
                                description=job["description"],
                                date=job["posted_date"]
                            )
                        except Exception:
                            pass
                    matches = search_matching_jobs(skills_list, n_results=10)

        # Show list of matches
        if not matches:
            st.info("No jobs found in index. Click 'Crawl & Index Tech Jobs' to fetch listings!")
            selected_match = None
        else:
            job_options = []
            for idx, m in enumerate(matches):
                meta = m.get("metadata", {})
                score_val = m.get("score", 0.5)
                # Normalize similarity score for display
                score_pct = max(0, min(100, int(score_val * 100))) if not search_query else None
                
                label_prefix = f"🎯 {score_pct}% Match" if score_pct is not None else f"📋 Job #{idx+1}"
                label = f"{label_prefix} | {meta.get('title')} at {meta.get('company')}"
                job_options.append({
                    "id": m["id"],
                    "label": label,
                    "job": m
                })
            
            selected_opt = st.radio(
                "Select Job listing:",
                options=job_options,
                format_func=lambda opt: opt["label"]
            )
            selected_match = selected_opt["job"] if selected_opt else None

            # Batch Submission Console UI Block
            st.divider()
            st.subheader("📦 Batch Submission Console")
            batch_selected = st.multiselect(
                "Select multiple jobs for Batch Submit:",
                options=job_options,
                format_func=lambda opt: opt["label"],
                key="batch_multiselect"
            )
            if batch_selected:
                submit_batch = st.checkbox("Enable actual submission for batch (uncheck for simulation)", value=False, key="batch_submit_mode")
                if st.button("Run Batch Application", type="primary", use_container_width=True):
                    log_area = st.empty()
                    progress_bar = st.progress(0.0)
                    log_text = "📦 **Starting Batch Processing...**\n"
                    log_area.markdown(log_text)
                    
                    total = len(batch_selected)
                    for idx, opt in enumerate(batch_selected):
                        job = opt["job"]
                        job_meta = job.get("metadata", {})
                        job_desc = job.get("document", "")
                        job_title = job_meta.get("title")
                        job_company = job_meta.get("company")
                        
                        # Find job url
                        job_url = ""
                        for j in st.session_state.crawled_jobs:
                            if j["title"] == job_title and j["company"] == job_company:
                                job_url = j.get("url", "")
                                break
                        
                        log_text += f"\n\n--- Processing Job {idx+1}/{total}: {job_title} at {job_company} ---"
                        log_area.markdown(log_text)
                        
                        try:
                            # 1. Tailor Resume
                            from agents.resume_tailor_agent import tailor_resume
                            tailored_res = tailor_resume(profile, job_desc)
                            
                            # 2. Compatibility Score
                            from agents.readiness_agent import evaluate_application_readiness
                            readiness_data = evaluate_application_readiness(profile, job_desc)
                            readiness_score = readiness_data.get("match_score", 50)
                            
                            # 3. ATS Score
                            from agents.ats_scorer_agent import ATSScorerAgent
                            scorer = ATSScorerAgent()
                            ats_data = scorer.evaluate_resume(tailored_res, job_desc)
                            ats_score = ats_data.get("ats_score", 50)
                            
                            # 4. Fill Application
                            from playwright.sync_api import sync_playwright
                            from agents.auto_submitter_agent import AutoSubmitterAgent
                            import re
                            
                            # Compile tailored resume PDF dynamically for this job in the batch
                            job_id = job.get("id", "unknown_job")
                            company_slug = re.sub(r'[\s/\\?%*:|"<>]', '_', job_company.lower())
                            job_out_dir = os.path.join("data", "tailored_applications", f"{company_slug}_{job_id}")
                            os.makedirs(job_out_dir, exist_ok=True)
                            
                            # Save tailored resume markdown
                            resume_md_path = os.path.join(job_out_dir, "resume_tailored.md")
                            with open(resume_md_path, "w", encoding="utf-8") as f:
                                f.write(tailored_res)
                            
                            # Compile PDF
                            resume_pdf_path = os.path.join(job_out_dir, "resume_tailored.pdf")
                            markdown_to_pdf(tailored_res, resume_pdf_path)
                            
                            agent = AutoSubmitterAgent(resume_path=resume_pdf_path)
                            abspath_test_form = os.path.abspath('scratch/test_form.html').replace('\\', '/')
                            target_url = job_url if job_url else f"file:///{abspath_test_form}"
                            
                            with sync_playwright() as p:
                                from tools.browser_launcher import launch_browser_with_context
                                browser, context, page = launch_browser_with_context(p, headless=True)
                                
                                job_id = job.get("id", "unknown_job")
                                metadata = {
                                    "company": job_company,
                                    "title": job_title,
                                    "readiness_score": readiness_score,
                                    "ats_score": ats_score,
                                    "job_id": job_id
                                }
                                
                                for entry in agent.fill_job_application(page, target_url, submit=submit_batch, metadata=metadata):
                                    log_text += f"\n- {entry}"
                                    log_area.markdown(log_text)
                                    
                                browser.close()
                                
                        except Exception as err:
                            log_text += f"\n- ❌ Failed: {err}"
                            log_area.markdown(log_text)
                            
                        progress_bar.progress((idx + 1) / total)
                        
                    st.success("Batch run completed!")

    with col2:
        if not selected_match:
            st.subheader("Job Details")
            st.info("Select a job listing from the left sidebar to view match analytics.")
        else:
            meta = selected_match.get("metadata", {})
            st.subheader(f"{meta.get('title')}")
            st.write(f"🏢 **Company:** {meta.get('company')} | 📍 **Location:** {meta.get('location')} | 📅 **Posted:** {meta.get('date')}")
            
            # Show original link
            url = None
            for job in st.session_state.crawled_jobs:
                if job["title"] == meta.get("title") and job["company"] == meta.get("company"):
                    url = job.get("url")
                    break
            
            if url:
                st.markdown(f"🔗 [View Original Job Posting]({url})")
            
            st.markdown("**Job Description:**")
            desc = selected_match.get("document", "")
            # Remove prefixes to show clean description text
            cleaned_desc = desc
            for prefix in [f"Job Title: {meta.get('title')}", f"Company: {meta.get('company')}", f"Location: {meta.get('location')}", "Description:"]:
                cleaned_desc = cleaned_desc.replace(prefix, "").strip()
            st.text_area("Description Text", cleaned_desc, height=150, disabled=True)
            
            st.divider()
            st.subheader("📊 Application Readiness Score")
            
            job_id = selected_match["id"]
            
            # Run Evaluation
            if st.button("Evaluate Readiness & Study Plan", type="primary", use_container_width=True):
                with st.spinner("Analyzing profile compatibility and writing readiness report..."):
                    from agents.readiness_agent import evaluate_application_readiness
                    evaluation = evaluate_application_readiness(profile, desc)
                    st.session_state.job_evaluations[job_id] = evaluation
            
            # Show evaluation if it exists in session state
            if job_id in st.session_state.job_evaluations:
                eval_data = st.session_state.job_evaluations[job_id]
                score = eval_data.get("match_score", 50)
                
                # Visual Match Score
                col_score, col_details = st.columns([1, 2])
                
                with col_score:
                    st.metric("Readiness Score", f"{score}%")
                    st.progress(score / 100.0)
                
                with col_details:
                    # Strengths
                    strengths = eval_data.get("strengths", [])
                    st.markdown("**Strengths:**")
                    if strengths:
                        badges = "".join([f'<p style="color:#15803d;font-weight:600;margin-bottom:4px;font-size:14px;">✓ {s}</p>' for s in strengths])
                        st.markdown(badges, unsafe_allow_html=True)
                    else:
                        st.write("None identified")
                        
                    # Gaps
                    gaps = eval_data.get("gaps", [])
                    st.markdown("**Gaps:**")
                    if gaps:
                        badges = "".join([f'<p style="color:#b91c1c;font-weight:600;margin-bottom:4px;font-size:14px;">✗ {s}</p>' for s in gaps])
                        st.markdown(badges, unsafe_allow_html=True)
                    else:
                        st.write("None identified (Perfect Match!)")
                
                st.divider()
                st.subheader("📚 Recommended Study Plan")
                recs = eval_data.get("recommendations", [])
                study_plan_text = ""
                if recs:
                    for idx, r in enumerate(recs, 1):
                        st.markdown(f"{idx}. {r}")
                        study_plan_text += f"{idx}. {r}\n"
                else:
                    st.write("No recommendations needed! You are fully prepared.")
                    study_plan_text = "No additional recommendations needed."
                
                # Build export text
                report_md = f"""# Application Readiness & Study Plan
**Job Title:** {meta.get('title')}
**Company:** {meta.get('company')}
**Readiness Score:** {score}%

## Strengths
{", ".join(strengths) if strengths else "None"}

## Gaps
{", ".join(gaps) if gaps else "None"}

---

## Study Plan
{study_plan_text}
"""
                
                # Exporters for readiness report
                st.divider()
                st.markdown("**Export Readiness Report:**")
                col_ex1, col_ex2 = st.columns(2)
                
                col_ex1.download_button(
                    label="Download Report (.md)",
                    data=report_md,
                    file_name=f"readiness_report_{meta.get('company').lower().replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
                
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        markdown_to_pdf(report_md, tmp.name)
                        with open(tmp.name, "rb") as f:
                            pdf_bytes = f.read()
                    col_ex2.download_button(
                        label="Download Report PDF (.pdf)",
                        data=pdf_bytes,
                        file_name=f"readiness_report_{meta.get('company').lower().replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    col_ex2.error(f"PDF creation failed: {e}")

                # ==================================================
                # RESUME TAILORING AGENT SECTION
                # ==================================================
                st.divider()
                st.subheader("✨ ATS Resume Tailoring Agent")
                st.markdown("Generate a customized, ATS-optimized version of your resume specifically tailored for this job description.")
                
                if "tailored_resumes" not in st.session_state:
                    st.session_state.tailored_resumes = {}
                
                # Tailor button
                if st.button("Tailor Resume for this Job", type="primary", use_container_width=True):
                    with st.spinner("Analyzing requirements and tailoring resume..."):
                        from agents.resume_tailor_agent import tailor_resume
                        tailored_res = tailor_resume(profile, desc)
                        st.session_state.tailored_resumes[job_id] = tailored_res
                
                # If tailored resume exists, display preview and download options
                if job_id in st.session_state.tailored_resumes:
                    tailored_content = st.session_state.tailored_resumes[job_id]
                    st.success("Resume tailored successfully!")
                    
                    # Ensure output directory exists
                    company_slug = re.sub(r'[\s/\\?%*:|"<>]', '_', meta.get('company').lower())
                    out_dir = os.path.join("data", "tailored_applications", f"{company_slug}_{job_id}")
                    os.makedirs(out_dir, exist_ok=True)
                    
                    # Bind editor key in session state
                    editor_key = f"tailored_resume_editor_{job_id}"
                    if editor_key not in st.session_state:
                        st.session_state[editor_key] = tailored_content
                        
                    # Save markdown file automatically to disk
                    resume_md_path = os.path.join(out_dir, "resume_tailored.md")
                    
                    # Two columns layout for live editor and preview
                    col_ed, col_prev = st.columns(2)
                    
                    with col_ed:
                        st.markdown("### ✏️ Live Markdown Editor")
                        edited_content = st.text_area(
                            "Edit your tailored resume content below. Changes are saved automatically.",
                            value=st.session_state[editor_key],
                            key=editor_key,
                            height=600
                        )
                        # Re-save to out_dir when changed
                        with open(resume_md_path, "w", encoding="utf-8") as f:
                            f.write(edited_content)
                            
                    with col_prev:
                        st.markdown("### 👁️ Live Preview")
                        st.markdown(
                            f'<div class="modern-card" style="height:628px; overflow-y:auto; border: 1px solid rgba(255,255,255,0.1); padding:20px; border-radius:8px; background:rgba(0,0,0,0.15); font-family:\'Inter\', sans-serif;">'
                            f'{markdown_to_html(edited_content)}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    
                    st.write("")
                    col_t1, col_t2, col_t3 = st.columns(3)
                    
                    col_t1.download_button(
                        label="Download Tailored (.md)",
                        data=edited_content,
                        file_name=f"resume_tailored_{meta.get('company').lower().replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                    
                    html_tailored = markdown_to_html(edited_content)
                    col_t2.download_button(
                        label="Download Tailored (.html)",
                        data=html_tailored,
                        file_name=f"resume_tailored_{meta.get('company').lower().replace(' ', '_')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            markdown_to_pdf(edited_content, tmp.name)
                            with open(tmp.name, "rb") as f:
                                pdf_tailored_bytes = f.read()
                        col_t3.download_button(
                            label="Download Tailored (.pdf)",
                            data=pdf_tailored_bytes,
                            file_name=f"resume_tailored_{meta.get('company').lower().replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        col_t3.error(f"Tailored PDF failed: {e}")

                    # ==================================================
                    # ATS SCORER CARD SECTION (Phase 5)
                    # ==================================================
                    st.divider()
                    st.subheader("📊 ATS Compatibility Card")
                    
                    if f"ats_report_{job_id}" not in st.session_state:
                        with st.spinner("Analyzing ATS scoring and formatting compatibility..."):
                            from agents.ats_scorer_agent import ATSScorerAgent
                            scorer = ATSScorerAgent()
                            st.session_state[f"ats_report_{job_id}"] = scorer.evaluate_resume(tailored_content, desc)
                            
                    ats_report = st.session_state[f"ats_report_{job_id}"]
                    ats_score = ats_report.get("ats_score", 50)
                    rating = ats_report.get("parsability_rating", "Excellent")
                    
                    col_score1, col_score2 = st.columns(2)
                    col_score1.metric("ATS Score", f"{ats_score}%")
                    col_score2.metric("Parsability Rating", rating)
                    
                    with st.expander("Show Keyword Analysis"):
                        st.markdown("**Matched Keywords:**")
                        st.write(", ".join(ats_report.get("matched_keywords", [])))
                        st.markdown("**Missing Keywords (Gaps):**")
                        st.write(", ".join(ats_report.get("missing_keywords", [])))
                        
                    st.markdown("**ATS Recommendations:**")
                    for rec in ats_report.get("recommendations", []):
                        st.markdown(f"- {rec}")

                    # ==================================================
                    # COVER LETTER SECTION (Phase 5)
                    # ==================================================
                    st.divider()
                    st.subheader("✉️ Tailored Cover Letter Agent")
                    st.markdown("Generate a cover letter specifically customized for this job listing.")
                    
                    if f"cover_letter_{job_id}" not in st.session_state:
                        st.session_state[f"cover_letter_{job_id}"] = None
                        
                    if st.button("Generate Tailored Cover Letter", key=f"cl_btn_{job_id}", type="primary", use_container_width=True):
                        with st.spinner("Drafting tailored cover letter..."):
                            from agents.cover_letter_agent import CoverLetterAgent
                            cl_agent = CoverLetterAgent()
                            st.session_state[f"cover_letter_{job_id}"] = cl_agent.generate_cover_letter(profile, desc)
                            
                    cl_content = st.session_state[f"cover_letter_{job_id}"]
                    if cl_content:
                        st.success("Cover Letter generated successfully!")
                        
                        col_c1, col_c2, col_c3 = st.columns(3)
                        col_c1.download_button(
                            label="Download Letter (.md)",
                            data=cl_content,
                            file_name=f"cover_letter_{meta.get('company').lower().replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                        
                        html_cl = markdown_to_html(cl_content)
                        col_c2.download_button(
                            label="Download Letter (.html)",
                            data=html_cl,
                            file_name=f"cover_letter_{meta.get('company').lower().replace(' ', '_')}.html",
                            mime="text/html",
                            use_container_width=True
                        )
                        
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                markdown_to_pdf(cl_content, tmp.name)
                                with open(tmp.name, "rb") as f:
                                    pdf_cl_bytes = f.read()
                            col_c3.download_button(
                                label="Download Letter (.pdf)",
                                data=pdf_cl_bytes,
                                file_name=f"cover_letter_{meta.get('company').lower().replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            col_c3.error(f"Letter PDF failed: {e}")
                            
                        st.markdown("**Cover Letter Preview:**")
                        st.markdown(cl_content)

                    # ==================================================
                    # AUTO-APPLY ASSISTANT SECTION
                    # ==================================================
                    st.divider()
                    st.subheader("🤖 Auto-Apply Assistant (Phase 4 & 5)")
                    st.markdown("Automate the application process by auto-filling form fields, uploading your PDF resume, and answering custom questions via the Gemini API.")
                    
                    submit_app = st.checkbox("Enable actual application submission (uncheck for simulation/fill-only mode)", value=False, key=f"submit_app_{job_id}")
                    
                    if st.button("Auto-Fill Application for this Job", type="secondary", use_container_width=True, key=f"autofill_btn_{job_id}"):
                        log_area = st.empty()
                        log_text = "🤖 **Auto-Apply Automation Log:**\n"
                        log_area.markdown(log_text)
                        
                        try:
                            from playwright.sync_api import sync_playwright
                            from agents.auto_submitter_agent import AutoSubmitterAgent
                            
                            # Compile the edited resume PDF dynamically for submission
                            resume_pdf_path = os.path.join(out_dir, "resume_tailored.pdf")
                            markdown_to_pdf(edited_content, resume_pdf_path)
                            
                            agent = AutoSubmitterAgent(resume_path=resume_pdf_path)
                            abspath_test_form = os.path.abspath('scratch/test_form.html').replace('\\', '/')
                            target_url = url if url else f"file:///{abspath_test_form}"
                            
                            metadata = {
                                "company": meta.get("company", "Unknown Company"),
                                "title": meta.get("title", "Unknown Title"),
                                "readiness_score": score,
                                "ats_score": ats_score,
                                "job_id": job_id
                            }
                            
                            with sync_playwright() as p:
                                from tools.browser_launcher import launch_browser_with_context
                                browser, context, page = launch_browser_with_context(p, headless=True)
                                
                                for log_entry in agent.fill_job_application(page, target_url, submit=submit_app, metadata=metadata):
                                    log_text += f"\n- {log_entry}"
                                    log_area.markdown(log_text)
                                    
                                browser.close()
                                
                            st.success("Auto-apply process completed!")
                        except Exception as apply_err:
                            st.error(f"Auto-apply failed: {apply_err}")

# ==================================================
# PAGE 7: HITL REVIEW QUEUE
# ==================================================
elif page == "HITL Review Queue":
    st.title("⏳ HITL Review Queue")
    st.markdown("Review and submit automated applications that are held pending manual approval. You can verify and edit custom answers generated by the Gemini API, inspect screenshots of the filled forms, and approve the submission live.")
    
    import os
    import json
    import re
    history_path = "data/application_history.json"
    
    if not os.path.exists(history_path):
        st.info("No application history found yet. Go to the 'Job Matcher' page and run applications, or let the daily background scheduler run!")
    else:
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            st.error(f"Failed to read application history: {e}")
            history = []
            
        pending_apps = [item for item in history if item.get("status") == "Pending Review"]
        
        if not pending_apps:
            st.success("🎉 You are all caught up! No applications are currently pending review.")
        else:
            st.warning(f"There are {len(pending_apps)} applications pending your manual review and approval.")
            
            for idx, app_item in enumerate(pending_apps):
                company = app_item.get("company", "Unknown Company")
                title = app_item.get("title", "Unknown Title")
                url = app_item.get("url", "")
                readiness_score = app_item.get("readiness_score", 50)
                ats_score = app_item.get("ats_score", 50)
                job_id = app_item.get("job_id", "")
                
                with st.container():
                    st.write("")
                    st.subheader(f"💼 {company} — {title}")
                    
                    col_left, col_right = st.columns([1, 1])
                    
                    # Resolve safe company slug
                    company_slug = re.sub(r'[\s/\\?%*:|"<>]', '_', company.lower())
                    q_json_path = os.path.join("data", "tailored_applications", f"{company_slug}_{job_id}", "custom_questions.json")
                    
                    custom_answers = {}
                    if os.path.exists(q_json_path):
                        try:
                            with open(q_json_path, "r", encoding="utf-8") as qf:
                                custom_answers = json.load(qf)
                        except Exception:
                            pass
                            
                    with col_left:
                        st.markdown(f"**Application URL:** [Apply Link]({url})")
                        st.markdown(f"**Readiness Score:** `{readiness_score}%` | **ATS Compatibility Score:** `{ats_score}%`")
                        
                        st.divider()
                        st.markdown("📝 **Custom Question Inputs & LLM Responses:**")
                        
                        updated_answers = {}
                        if custom_answers:
                            for question, ans_val in custom_answers.items():
                                # Unique widget key
                                key_id = f"hitl_{job_id}_{hash(question)}"
                                user_ans = st.text_area(f"❓ {question}", value=ans_val, key=key_id, height=120)
                                updated_answers[question] = user_ans
                        else:
                            st.info("No custom essay questions were encountered for this application form.")
                            
                        # Review Actions
                        st.write("")
                        col_act1, col_act2 = st.columns(2)
                        
                        if col_act1.button("✅ Approve & Submit", key=f"app_sub_{job_id}", type="primary", use_container_width=True):
                            with st.spinner("Re-filling form fields and executing live submission..."):
                                if updated_answers:
                                    try:
                                        with open(q_json_path, "w", encoding="utf-8") as qf:
                                            json.dump(updated_answers, qf, indent=2)
                                    except Exception:
                                        pass
                                        
                                from playwright.sync_api import sync_playwright
                                from agents.auto_submitter_agent import AutoSubmitterAgent
                                from tools.browser_launcher import launch_browser_with_context
                                from tools.notifier import send_notification
                                
                                resume_pdf_path = os.path.join("data", "tailored_applications", f"{company_slug}_{job_id}", "resume_tailored.pdf")
                                if not os.path.exists(resume_pdf_path):
                                    resume_pdf_path = "Resume.pdf"
                                    
                                agent = AutoSubmitterAgent(
                                    profile_path="data/master_profile.json",
                                    resume_path=resume_pdf_path,
                                    prefilled_answers=updated_answers
                                )
                                
                                log_area = st.empty()
                                log_text = "🤖 **Submitting Application Live:**\n"
                                log_area.markdown(log_text)
                                
                                try:
                                    with sync_playwright() as p:
                                        browser, context, page = launch_browser_with_context(p, headless=True)
                                        
                                        metadata = {
                                            "company": company,
                                            "title": title,
                                            "readiness_score": readiness_score,
                                            "ats_score": ats_score,
                                            "job_id": job_id
                                        }
                                        
                                        for log_entry in agent.fill_job_application(page, url, submit=True, metadata=metadata):
                                            log_text += f"\n- {log_entry}"
                                            log_area.markdown(log_text)
                                            
                                        browser.close()
                                        
                                    st.success("Application successfully submitted live!")
                                    send_notification(f"Submitted application for **{company}** - *{title}* (Readiness: {readiness_score}%, ATS: {ats_score}%)", "success")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Live submission failed: {e}")
                                    send_notification(f"Failed to submit application for **{company}** - *{title}*: {e}", "error")
                                    
                        if col_act2.button("🗑️ Discard Application", key=f"discard_{job_id}", type="secondary", use_container_width=True):
                            if os.path.exists(history_path):
                                try:
                                    with open(history_path, "r", encoding="utf-8") as f:
                                        hist = json.load(f)
                                    for idx_h, item in enumerate(hist):
                                        if item.get("job_id") == job_id:
                                            hist[idx_h]["status"] = "Discarded"
                                            break
                                    with open(history_path, "w", encoding="utf-8") as f:
                                        json.dump(hist, f, indent=2)
                                    st.toast(f"Discarded application for {company}.")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"Failed to discard application: {err}")
                                    
                    with col_right:
                        st.markdown("📸 **Filled Page Screenshot Preview:**")
                        screenshot_path = os.path.join("data", "tailored_applications", f"{company_slug}_{job_id}", "screenshot.png")
                        if os.path.exists(screenshot_path):
                            st.image(screenshot_path, caption="Page Screenshot (Form State)", use_container_width=True)
                        else:
                            st.info("No screenshot captured for this application form state.")
                
                st.divider()

# ==================================================
# PAGE 8: APPLICATION ANALYTICS
# ==================================================
elif page == "Application Analytics":
    st.title("📊 Application History & Submission Analytics")
    st.markdown("Track and visualize your automated job submissions, matching scores, and application outcomes.")
    
    import pandas as pd
    history_path = "data/application_history.json"
    
    if not os.path.exists(history_path):
        st.info("No application history found yet. Go to the 'Job Matcher' page and run auto-apply or batch submissions!")
    else:
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            st.error(f"Failed to read application history: {e}")
            history = []
            
        if not history:
            st.info("Your application history is empty. Submit some applications first!")
        else:
            df = pd.DataFrame(history)
            
            # KPI Metrics Row
            col1, col2, col3, col4 = st.columns(4)
            
            total_apps = len(df)
            col1.metric("Total Runs", total_apps)
            
            submitted_count = len(df[df["status"] == "Submitted"])
            simulated_count = len(df[df["status"] == "Simulated"])
            failed_count = len(df[df["status"] == "Failed"])
            
            col2.metric("Submitted Applications", submitted_count)
            col3.metric("Simulation Runs", simulated_count)
            col4.metric("Failed Runs", failed_count)
            
            # Score Metrics Row
            st.write("")
            col_s1, col_s2, col_s3 = st.columns(3)
            avg_readiness = int(df["readiness_score"].mean()) if "readiness_score" in df else 50
            avg_ats = int(df["ats_score"].mean()) if "ats_score" in df else 50
            success_rate = int((submitted_count + simulated_count) / total_apps * 100) if total_apps > 0 else 0
            
            col_s1.metric("Avg Readiness Score", f"{avg_readiness}%")
            col_s2.metric("Avg ATS Score", f"{avg_ats}%")
            col_s3.metric("Process Success Rate", f"{success_rate}%")
            
            # Render Charts
            st.divider()
            st.subheader("Trends & Visual Analytics")
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("**Submission Status Breakdown:**")
                status_counts = df["status"].value_counts().reset_index()
                status_counts.columns = ["Status", "Count"]
                st.bar_chart(status_counts.set_index("Status"))
                
            with chart_col2:
                st.markdown("**Readiness vs ATS Scores (Chronological):**")
                score_df = df[["timestamp", "readiness_score", "ats_score"]].copy()
                score_df = score_df.rename(columns={"readiness_score": "Readiness Score", "ats_score": "ATS Score"})
                st.line_chart(score_df.set_index("timestamp"))
                
            # Date-grouped daily summary
            st.divider()
            st.subheader("📅 Daily Applications Summary")
            
            # Extract date (YYYY-MM-DD) from timestamp
            df["date"] = df["timestamp"].str.split(" ").str[0]
            
            daily_col1, daily_col2 = st.columns([1.5, 1.2])
            
            with daily_col1:
                st.markdown("**Applications Count by Date:**")
                daily_counts = df.groupby("date").size().reset_index(name="Applications")
                st.bar_chart(daily_counts.set_index("date"))
                
            with daily_col2:
                st.markdown("**Daily Status Breakdown Table:**")
                daily_breakdown = df.groupby(["date", "status"]).size().unstack(fill_value=0)
                # Ensure standard statuses exist in columns for consistency
                for s in ["Submitted", "Simulated", "Pending Review", "Failed"]:
                    if s not in daily_breakdown.columns:
                        daily_breakdown[s] = 0
                # Re-order and sort descending
                daily_breakdown = daily_breakdown[["Submitted", "Simulated", "Pending Review", "Failed"]].sort_index(ascending=False)
                st.dataframe(daily_breakdown, use_container_width=True)
                
            # Log Table
            st.divider()
            st.subheader("📋 Application History Log")
            st.dataframe(df.sort_values(by="timestamp", ascending=False), use_container_width=True)


