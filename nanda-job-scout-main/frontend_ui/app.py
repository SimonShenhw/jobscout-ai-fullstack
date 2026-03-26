import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from api_client import run_pipeline

# ==============================================
# Page config
# ==============================================
st.set_page_config(
    page_title="Job Scout AI",
    page_icon="🎯",
    layout="wide",
)

# ==============================================
# Load custom CSS
# ==============================================
with open("style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ==============================================
# Initialize session state
# ==============================================
if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None
if "interview_prep" not in st.session_state:
    st.session_state.interview_prep = []
if "resume_tips" not in st.session_state:
    st.session_state.resume_tips = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "is_live" not in st.session_state:
    st.session_state.is_live = False

# ==============================================
# Sidebar — User inputs
# ==============================================
with st.sidebar:
    st.markdown("# 🎯 Job Scout AI")
    st.markdown(
        "<p style='color:#9090B0; font-size:0.85rem; margin-top:-10px;'>"
        "AI-powered job search & interview prep</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    location = st.text_input(
        "📍 LOCATION",
        value="Greater Boston Area",
        placeholder="e.g. Greater Boston Area",
    )

    keywords = st.text_input(
        "🔑 KEYWORDS",
        value="Data Scientist AI Intern",
        placeholder="e.g. Data Scientist AI Intern",
    )

    num_results = st.slider(
        "📊 NUMBER OF RESULTS",
        min_value=1,
        max_value=10,
        value=3,
    )

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📄 UPLOAD RESUME",
        type=["pdf", "txt"],
        help="Upload your resume to get personalized interview questions",
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.type == "text/plain":
                st.session_state.resume_text = uploaded_file.read().decode("utf-8")
            else:
                reader = PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                st.session_state.resume_text = text.strip()

            if st.session_state.resume_text:
                st.success(f"✅ {uploaded_file.name}")
                with st.expander("📄 Preview extracted text"):
                    st.text(st.session_state.resume_text[:500] + "...")
            else:
                st.warning("⚠️ Could not extract text from this file.")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

    st.markdown("---")

    scout_button = st.button(
        "🔍  Scout Jobs", use_container_width=True, type="primary"
    )

    # Show connection status
    if "is_live" in st.session_state and st.session_state.is_live:
        st.markdown(
            "<div style='background:#D1FAE5; color:#065F46; padding:6px 12px;"
            " border-radius:8px; font-size:0.75rem; text-align:center;'>"
            "🟢 Connected to live server</div>",
            unsafe_allow_html=True,
        )
    elif st.session_state.jobs:
        st.markdown(
            "<div style='background:#FEF3C7; color:#92400E; padding:6px 12px;"
            " border-radius:8px; font-size:0.75rem; text-align:center;'>"
            "🟡 Demo mode — using sample data</div>",
            unsafe_allow_html=True,
        )

    # Footer
    st.markdown(
        "<div style='position:fixed; bottom:16px; left:16px; "
        "font-size:0.7rem; color:#6B6B8D;'>"
        "Built with Streamlit • AAI 5025 Group Project"
        "</div>",
        unsafe_allow_html=True,
    )

# ==============================================
# Main content area
# ==============================================

# Header
st.markdown("# 🎯 Job Scout AI")
st.markdown(
    "Discover tech internships and prepare for interviews — all powered by AI."
)

# Handle the scout button click
if scout_button:
    if not location.strip():
        st.warning("⚠️ Please enter a location.")
    elif not keywords.strip():
        st.warning("⚠️ Please enter at least one keyword.")
    else:
        with st.spinner("🔍 Running full pipeline... (first request may take up to 60s while server wakes up)"):
            result = run_pipeline(location, keywords, num_results, st.session_state.resume_text)

        if result["status"] == "success" and result["jobs"]:
            st.session_state.jobs = result["jobs"]
            st.session_state.resume_tips = result.get("resume_tips", [])
            st.session_state.interview_prep = result.get("interview_prep", [])
            st.session_state.is_live = result.get("is_live", False)
            st.session_state.selected_job = None
            st.session_state.chat_history = []

            if result.get("errors"):
                for err in result["errors"]:
                    st.warning(f"⚠️ {err}")

            if not result.get("is_live"):
                st.info("ℹ️ Server is not available yet — showing demo data.")
        elif result.get("message"):
            st.error(f"❌ {result['message']}")
        else:
            st.error("❌ No jobs found. Try different keywords or location.")

# ==============================================
# Stats row
# ==============================================
if st.session_state.jobs:
    st.markdown("## 📊 Search Results")

    col1, col2, col3 = st.columns(3)
    jobs = st.session_state.jobs

    col1.metric("Jobs Found", len(jobs))

    all_skills = []
    for j in jobs:
        all_skills.extend(j.get("core_skills", []))
    col2.metric("Unique Skills", len(set(all_skills)))

    col3.metric("Companies", len(set(j.get("company", "") for j in jobs)))

    st.markdown("")  # spacer

    # ==============================================
    # Job cards
    # ==============================================
    for i, job in enumerate(jobs):
        with st.container():
            badges = "".join(
                f"<span class='skill-badge'>{s}</span>"
                for s in job.get("core_skills", [])
            )

            salary = job.get("estimated_salary", "Not Specified")
            salary_html = (
                f"<span class='salary-badge'>{salary}</span>"
                if salary and salary != "Not Specified"
                else "<span class='salary-badge salary-na'>Not Specified</span>"
            )

            st.markdown(
                f"""
                <div style='background:white; border:1px solid #E5E7EB;
                     border-radius:12px; padding:1.2rem 1.5rem;
                     margin-bottom:0.8rem;
                     box-shadow: 0 1px 3px rgba(0,0,0,0.04);'>
                    <div style='display:flex; justify-content:space-between;
                          align-items:start;'>
                        <div>
                            <h3 style='margin:0 0 4px 0; font-size:1.05rem;
                                 color:#1E1E2E;'>{job.get("job_title", "")}</h3>
                            <p style='margin:0; color:#6C63FF; font-weight:600;
                                font-size:0.9rem;'>{job.get("company", "")}</p>
                        </div>
                        <a href='{job.get("apply_link", "#")}' target='_blank'
                           style='background:#6C63FF; color:white;
                           padding:6px 16px; border-radius:8px;
                           text-decoration:none; font-size:0.82rem;
                           font-weight:600; white-space:nowrap;'>
                            Apply →
                        </a>
                    </div>
                    <div style='margin:8px 0 6px;'>{salary_html}</div>
                    <p style='margin:6px 0 8px; color:#555;
                        font-size:0.88rem;'>{job.get("summary", "")}</p>
                    <div>{badges}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ==============================================
    # Resume Tips section
    # ==============================================
    if st.session_state.resume_tips:
        st.markdown("## 💡 Resume Tips")
        for tip in st.session_state.resume_tips:
            st.markdown(
                f"<div style='background:#F0FDF4; border-left:3px solid #22C55E;"
                f" border-radius:8px; padding:10px 14px; margin-bottom:8px;"
                f" font-size:0.88rem; color:#166534;'>{tip}</div>",
                unsafe_allow_html=True,
            )

    # ==============================================
    # Interview prep section
    # ==============================================
    st.markdown("## 🎤 Interview Prep")

    job_options = [
        f"{j.get('company', '')} — {j.get('job_title', '')}" for j in st.session_state.jobs
    ]
    selected = st.selectbox(
        "Select a job to practice for:", job_options, label_visibility="collapsed"
    )
    selected_index = job_options.index(selected)
    st.session_state.selected_job = st.session_state.jobs[selected_index]

    # Show selected job context
    sel = st.session_state.selected_job
    st.markdown(
        f"<div style='background:#F0EDFF; border-radius:10px; padding:12px 16px;"
        f" font-size:0.88rem; color:#4338CA; margin-bottom:1rem;'>"
        f"Preparing questions for <strong>{sel.get('job_title', '')}</strong> "
        f"at <strong>{sel.get('company', '')}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Find matching interview prep from pipeline results
    prep_for_job = None
    for prep in st.session_state.interview_prep:
        if (prep.get("company") == sel.get("company")
                and prep.get("job_title") == sel.get("job_title")):
            prep_for_job = prep
            break

    if prep_for_job:
        # Show candidate highlights
        highlights = prep_for_job.get("candidate_highlights", [])
        if highlights:
            st.markdown("**Candidate Highlights:**")
            for h in highlights:
                st.markdown(f"- {h}")

        # Show full interview questions with category and rationale
        questions = prep_for_job.get("questions", [])
        if questions:
            st.markdown("**Interview Questions:**")
            for idx, q in enumerate(questions, 1):
                category = q.get("category", "General") if isinstance(q, dict) else "General"
                question = q.get("question", str(q)) if isinstance(q, dict) else str(q)
                rationale = q.get("rationale", "") if isinstance(q, dict) else ""

                cat_colors = {
                    "Technical": ("#DBEAFE", "#1E40AF"),
                    "Behavioral": ("#FEF3C7", "#92400E"),
                    "Role-Specific": ("#E0E7FF", "#3730A3"),
                }
                bg, fg = cat_colors.get(category, ("#F3F4F6", "#374151"))

                st.markdown(
                    f"<div style='background:white; border:1px solid #E5E7EB;"
                    f" border-radius:10px; padding:12px 16px; margin-bottom:10px;'>"
                    f"<span style='background:{bg}; color:{fg}; padding:2px 10px;"
                    f" border-radius:12px; font-size:0.75rem; font-weight:600;'>"
                    f"{category}</span>"
                    f"<p style='margin:8px 0 4px; font-size:0.92rem; color:#1E1E2E;'>"
                    f"<strong>Q{idx}:</strong> {question}</p>"
                    f"<p style='margin:0; font-size:0.8rem; color:#6B7280; font-style:italic;'>"
                    f"{rationale}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Populate chat history from questions
            if not st.session_state.chat_history:
                for q in questions:
                    question_text = q.get("question", str(q)) if isinstance(q, dict) else str(q)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": question_text}
                    )
    else:
        st.info("💡 Interview questions will appear here after running the pipeline.")

    # ==============================================
    # Chat interface
    # ==============================================
    if st.session_state.chat_history:
        st.markdown("## 💬 Interview Chat")
        st.caption("Answer the questions below to practice for your interview.")

        for msg in st.session_state.chat_history:
            with st.chat_message(
                msg["role"],
                avatar="🤖" if msg["role"] == "assistant" else "👤",
            ):
                st.write(msg["content"])

        user_answer = st.chat_input("Type your answer here...")
        if user_answer:
            st.session_state.chat_history.append(
                {"role": "user", "content": user_answer}
            )
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": "Great answer! Think about how you could "
                    "add a specific example with measurable results "
                    "to make it even stronger. 💡",
                }
            )
            st.rerun()

# ==============================================
# Empty state — landing page
# ==============================================
else:
    st.markdown("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style='text-align:center; padding:2rem 1rem;
                 background:white; border:1px solid #E5E7EB;
                 border-radius:12px;'>
                <div style='font-size:2.5rem; margin-bottom:0.5rem;'>🔍</div>
                <h3 style='margin:0 0 6px;'>Discover</h3>
                <p style='color:#666; font-size:0.85rem; margin:0;'>
                    Search tech internships tailored to your skills
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style='text-align:center; padding:2rem 1rem;
                 background:white; border:1px solid #E5E7EB;
                 border-radius:12px;'>
                <div style='font-size:2.5rem; margin-bottom:0.5rem;'>📄</div>
                <h3 style='margin:0 0 6px;'>Match</h3>
                <p style='color:#666; font-size:0.85rem; margin:0;'>
                    Upload your resume for personalized results
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div style='text-align:center; padding:2rem 1rem;
                 background:white; border:1px solid #E5E7EB;
                 border-radius:12px;'>
                <div style='font-size:2.5rem; margin-bottom:0.5rem;'>🎤</div>
                <h3 style='margin:0 0 6px;'>Prepare</h3>
                <p style='color:#666; font-size:0.85rem; margin:0;'>
                    Practice with AI-generated interview questions
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.info("👈 Enter your search criteria in the sidebar and click **Scout Jobs** to get started.")
