"""
[ZH] 岗位卡片组件 / [EN] Job card component
"""
import streamlit as st


def _build_cost_html(job: dict, cost_of_living: list) -> str:
    """[ZH] 构建生活成本 HTML / [EN] Build cost of living HTML."""
    for col in cost_of_living:
        if (col.get("company") == job.get("company")
                and col.get("job_title") == job.get("job_title")):
            aff = col.get("affordability", "")
            if "Comfortable" in aff:
                aff_color, aff_bg = "#065F46", "#ECFDF5"
            elif "Moderate" in aff:
                aff_color, aff_bg = "#92400E", "#FEF3C7"
            elif "Tight" in aff:
                aff_color, aff_bg = "#991B1B", "#FEE2E2"
            else:
                aff_color, aff_bg = "#6B7280", "#F3F4F6"

            ai_comment = col.get("ai_comment", "")
            monthly_cost = col.get("monthly_cost_range", "")
            monthly_surplus = col.get("monthly_surplus_range", "")
            details = []
            if monthly_cost:
                details.append(f"Monthly Cost: {monthly_cost}")
            if monthly_surplus:
                details.append(f"Surplus: {monthly_surplus}")
            details_str = " | ".join(details)

            return (
                f"<div style='margin:6px 0; padding:8px 12px; background:{aff_bg};"
                f" border-radius:8px; font-size:0.82rem; color:{aff_color};'>"
                f"<strong>Cost of Living:</strong> {aff}"
                f"{f' ({details_str})' if details_str else ''}"
                f"{f'<br><em>{ai_comment}</em>' if ai_comment else ''}"
                f"</div>"
            )
    return ""


def render_job_card(job: dict, cost_of_living: list) -> None:
    """
    [ZH] 渲染单个岗位卡片，包含薪资、生活成本、技能、申请链接
    [EN] Render a single job card with salary, cost of living, skills, apply link
    """
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

    cost_html = _build_cost_html(job, cost_of_living)

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
            {cost_html}
            <p style='margin:6px 0 8px; color:#555;
                font-size:0.88rem;'>{job.get("summary", "")}</p>
            <div>{badges}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
