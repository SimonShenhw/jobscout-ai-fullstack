"""
[ZH] JobScout AI 前端入口（已拆分为 components 模块）
[EN] JobScout AI frontend entry point (modularized into components)
"""
import os
import streamlit as st

from api_client import run_pipeline
from components import (
    render_job_card,
    render_resume_tips,
    render_interview_panel,
    render_sidebar,
    render_landing,
)


# ==============================================
# [ZH] 页面配置 / [EN] Page config
# ==============================================
st.set_page_config(
    page_title="Job Scout AI",
    page_icon="🎯",
    layout="wide",
)


# ==============================================
# [ZH] 加载自定义 CSS / [EN] Load custom CSS
# ==============================================
_css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
with open(_css_path, encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ==============================================
# [ZH] 初始化 session state / [EN] Initialize session state
# ==============================================
def _init_state() -> None:
    defaults = {
        "jobs": [],
        "selected_job": None,
        "interview_prep": [],
        "resume_tips": [],
        "cost_of_living": [],
        "chat_history": [],
        "resume_text": "",
        "is_live": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()


# ==============================================
# [ZH] 侧边栏 / [EN] Sidebar
# ==============================================
location, keywords, num_results, scout_button = render_sidebar()


# ==============================================
# [ZH] 主区域 - 标题 / [EN] Main - header
# ==============================================
st.markdown("# 🎯 Job Scout AI")
st.markdown(
    "Discover tech internships and prepare for interviews — all powered by AI."
)


# ==============================================
# [ZH] 处理 Scout 按钮点击 / [EN] Handle scout button
# ==============================================
def _run_pipeline_with_progress() -> None:
    """[ZH] 跑流水线并展示分步进度 / [EN] Run pipeline with stepwise progress."""
    progress_placeholder = st.empty()
    with progress_placeholder.container():
        with st.status("🔍 Running A2A pipeline...", expanded=True) as status:
            st.write("⏳ Step 1/4: Scouting jobs (SerpAPI + Gemini)...")
            st.write("⏳ Step 2/4: Retrieving resume tips (Vector DB)...")
            st.write("⏳ Step 3/4: Generating interview questions (Gemini)...")
            st.write("⏳ Step 4/4: Evaluating cost of living (Agent B)...")
            result = run_pipeline(location, keywords, num_results, st.session_state.resume_text)
            status.update(label="✅ Pipeline complete!", state="complete", expanded=False)
    progress_placeholder.empty()

    if result["status"] == "success" and result["jobs"]:
        st.session_state.jobs = result["jobs"]
        st.session_state.resume_tips = result.get("resume_tips", [])
        st.session_state.interview_prep = result.get("interview_prep", [])
        st.session_state.cost_of_living = result.get("cost_of_living", [])
        st.session_state.is_live = result.get("is_live", False)
        st.session_state.selected_job = None
        st.session_state.chat_history = []

        for err in result.get("errors", []):
            st.warning(f"⚠️ {err}")

        if not result.get("is_live"):
            st.info("ℹ️ Server is not available yet — showing demo data.")
    elif result.get("message"):
        st.error(f"❌ {result['message']}")
    else:
        st.error("❌ No jobs found. Try different keywords or location.")


if scout_button:
    if not location.strip():
        st.warning("⚠️ Please enter a location.")
    elif not keywords.strip():
        st.warning("⚠️ Please enter at least one keyword.")
    else:
        _run_pipeline_with_progress()


# ==============================================
# [ZH] 结果展示 / [EN] Results display
# ==============================================
if st.session_state.jobs:
    st.markdown("## 📊 Search Results")

    col1, col2, col3 = st.columns(3)
    jobs = st.session_state.jobs

    col1.metric("Jobs Found", len(jobs))
    all_skills = [s for j in jobs for s in j.get("core_skills", [])]
    col2.metric("Unique Skills", len(set(all_skills)))
    col3.metric("Companies", len(set(j.get("company", "") for j in jobs)))

    st.markdown("")

    # [ZH] 岗位卡片 / [EN] Job cards
    for job in jobs:
        with st.container():
            render_job_card(job, st.session_state.cost_of_living)

    # [ZH] 简历建议 / [EN] Resume tips
    render_resume_tips(st.session_state.resume_tips)

    # [ZH] 面试准备 / [EN] Interview prep
    render_interview_panel(jobs, st.session_state.interview_prep)

else:
    # [ZH] 着陆页 / [EN] Landing page
    render_landing()
