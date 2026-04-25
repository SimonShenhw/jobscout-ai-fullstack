"""
[ZH] 简历建议组件 / [EN] Resume tips component
"""
import streamlit as st


def render_resume_tips(tips: list) -> None:
    """[ZH] 渲染简历建议列表 / [EN] Render the resume tips list."""
    if not tips:
        return

    st.markdown("## 💡 Resume Tips")
    for tip in tips:
        st.markdown(
            f"<div style='background:#F0FDF4; border-left:3px solid #22C55E;"
            f" border-radius:8px; padding:10px 14px; margin-bottom:8px;"
            f" font-size:0.88rem; color:#166534;'>{tip}</div>",
            unsafe_allow_html=True,
        )
