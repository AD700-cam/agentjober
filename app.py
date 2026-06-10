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

# Load profile data
try:
    profile = load_profile()
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
        from scrapers.job_scraper import scrape_jobs
        
        scheduler = BackgroundScheduler()
        # Schedule the Playwright scraper to run daily at 8:00 AM
        scheduler.add_job(scrape_jobs, "cron", hour=8, minute=0, args=[15])
        scheduler.start()
        print("[Scheduler] Started background daily job crawler at 8:00 AM.")
        return scheduler
    except Exception as e:
        print(f"[Scheduler] Failed to start background scheduler: {e}")
        return None

scheduler = start_scheduler()

# App title and sidebar navigation
st.sidebar.title("🎓 AI Career Assistant")
st.sidebar.markdown("Navigate through your AI agents:")

page = st.sidebar.radio(
    "Choose Agent:",
    ["Profile Assistant", "Resume Generator", "Portfolio Generator", "Interview Coach", "Career Advisor", "Job Matcher"]
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
                    
                    col_t1, col_t2, col_t3 = st.columns(3)
                    
                    col_t1.download_button(
                        label="Download Tailored (.md)",
                        data=tailored_content,
                        file_name=f"resume_tailored_{meta.get('company').lower().replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                    
                    html_tailored = markdown_to_html(tailored_content)
                    col_t2.download_button(
                        label="Download Tailored (.html)",
                        data=html_tailored,
                        file_name=f"resume_tailored_{meta.get('company').lower().replace(' ', '_')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            markdown_to_pdf(tailored_content, tmp.name)
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
                    
                    st.markdown("**Tailored Resume Preview:**")
                    st.markdown(tailored_content)
