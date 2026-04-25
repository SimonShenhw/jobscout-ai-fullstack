"""
[ZH] 侧边栏组件（用户输入 + 简历上传）
[EN] Sidebar component (user inputs + resume upload)
"""
import streamlit as st
from PyPDF2 import PdfReader


def render_sidebar() -> tuple[str, str, int, bool]:
    """
    [ZH] 渲染侧边栏，返回 (location, keywords, num_results, scout_button)
    [EN] Render sidebar, returns (location, keywords, num_results, scout_button)
    """
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

        _handle_resume_upload()

        st.markdown("---")

        scout_button = st.button(
            "🔍  Scout Jobs", use_container_width=True, type="primary"
        )

        _show_connection_status()
        _show_footer()

    return location, keywords, num_results, scout_button


def _handle_resume_upload() -> None:
    """[ZH] 处理简历上传 / [EN] Handle resume upload."""
    uploaded_file = st.file_uploader(
        "📄 UPLOAD RESUME",
        type=["pdf", "txt"],
        help="Upload your resume to get personalized interview questions",
    )

    if uploaded_file is None:
        return

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


def _show_connection_status() -> None:
    """[ZH] 显示连接状态 / [EN] Show connection status."""
    if st.session_state.get("is_live"):
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


def _show_footer() -> None:
    """[ZH] 侧边栏 footer / [EN] Sidebar footer."""
    st.markdown(
        "<div style='position:fixed; bottom:16px; left:16px; "
        "font-size:0.7rem; color:#6B6B8D;'>"
        "Built with Streamlit • AAI 5025 Group Project"
        "</div>",
        unsafe_allow_html=True,
    )
