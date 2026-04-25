"""
[ZH] 着陆页组件（无搜索结果时展示）
[EN] Landing page component (shown when no results yet)
"""
import streamlit as st


_FEATURE_CARDS = [
    ("🔍", "Discover", "Search tech internships tailored to your skills"),
    ("📄", "Match",    "Upload your resume for personalized results"),
    ("🎤", "Prepare",  "Practice with AI-generated interview questions"),
]


def render_landing() -> None:
    """[ZH] 渲染着陆页 / [EN] Render the landing page."""
    st.markdown("")
    cols = st.columns(3)
    for col, (icon, title, desc) in zip(cols, _FEATURE_CARDS):
        with col:
            st.markdown(
                f"""
                <div style='text-align:center; padding:2rem 1rem;
                     background:white; border:1px solid #E5E7EB;
                     border-radius:12px;'>
                    <div style='font-size:2.5rem; margin-bottom:0.5rem;'>{icon}</div>
                    <h3 style='margin:0 0 6px;'>{title}</h3>
                    <p style='color:#666; font-size:0.85rem; margin:0;'>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")
    st.info("👈 Enter your search criteria in the sidebar and click **Scout Jobs** to get started.")
