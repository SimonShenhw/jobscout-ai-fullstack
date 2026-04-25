"""
[ZH] 面试准备面板组件（包含问题展示和聊天）
[EN] Interview prep panel (questions display + chat)
"""
import streamlit as st
from api_client import get_interview_feedback


CATEGORY_COLORS = {
    "Technical":     ("#DBEAFE", "#1E40AF"),
    "Behavioral":    ("#FEF3C7", "#92400E"),
    "Role-Specific": ("#E0E7FF", "#3730A3"),
}


def _render_question(idx: int, q: dict | str) -> None:
    """[ZH] 渲染单道面试题 / [EN] Render a single interview question."""
    if isinstance(q, dict):
        category = q.get("category", "General")
        question = q.get("question", str(q))
        rationale = q.get("rationale", "")
    else:
        category, question, rationale = "General", str(q), ""

    bg, fg = CATEGORY_COLORS.get(category, ("#F3F4F6", "#374151"))

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


def _find_prep_for_job(interview_prep: list, job: dict) -> dict | None:
    """[ZH] 查找指定岗位的面试题 / [EN] Find prep matching the given job."""
    for prep in interview_prep:
        if (prep.get("company") == job.get("company")
                and prep.get("job_title") == job.get("job_title")):
            return prep
    return None


def render_interview_panel(jobs: list, interview_prep: list) -> None:
    """[ZH] 渲染面试准备面板 / [EN] Render the interview prep panel."""
    st.markdown("## 🎤 Interview Prep")

    job_options = [f"{j.get('company', '')} — {j.get('job_title', '')}" for j in jobs]
    selected = st.selectbox(
        "Select a job to practice for:", job_options, label_visibility="collapsed"
    )
    selected_index = job_options.index(selected)
    sel = jobs[selected_index]
    st.session_state.selected_job = sel

    # [ZH] 显示选中岗位上下文 / [EN] Show selected job context
    st.markdown(
        f"<div style='background:#F0EDFF; border-radius:10px; padding:12px 16px;"
        f" font-size:0.88rem; color:#4338CA; margin-bottom:1rem;'>"
        f"Preparing questions for <strong>{sel.get('job_title', '')}</strong> "
        f"at <strong>{sel.get('company', '')}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    prep_for_job = _find_prep_for_job(interview_prep, sel)

    if prep_for_job:
        # [ZH] 候选人亮点 / [EN] Candidate highlights
        highlights = prep_for_job.get("candidate_highlights", [])
        if highlights:
            st.markdown("**Candidate Highlights:**")
            for h in highlights:
                st.markdown(f"- {h}")

        # [ZH] 完整面试题 / [EN] Full interview questions
        questions = prep_for_job.get("questions", [])
        if questions:
            st.markdown("**Interview Questions:**")
            for idx, q in enumerate(questions, 1):
                _render_question(idx, q)

            # [ZH] 把问题填进聊天历史（仅首次）/ [EN] Populate chat once
            if not st.session_state.chat_history:
                for q in questions:
                    text = q.get("question", str(q)) if isinstance(q, dict) else str(q)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": text}
                    )
    else:
        st.info("💡 Interview questions will appear here after running the pipeline.")

    # [ZH] 聊天界面 / [EN] Chat interface
    if st.session_state.chat_history:
        _render_chat(sel)


def _render_chat(selected_job: dict) -> None:
    """[ZH] 渲染聊天界面 / [EN] Render the chat interface."""
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

        # [ZH] 找到正在回答的问题 / [EN] Find the question being answered
        current_question = ""
        for msg in reversed(st.session_state.chat_history[:-1]):
            if msg["role"] == "assistant":
                current_question = msg["content"]
                break

        with st.spinner("🤔 Analyzing your answer..."):
            feedback = get_interview_feedback(
                question=current_question,
                answer=user_answer,
                job_title=selected_job.get("job_title", ""),
                company=selected_job.get("company", ""),
            )

        score = feedback.get("score", 0)
        feedback_text = feedback.get("feedback", "")
        score_emoji = "🌟" if score >= 8 else "👍" if score >= 6 else "💡"

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": f"{score_emoji} **Score: {score}/10**\n\n{feedback_text}",
            }
        )
        st.rerun()
