import os
import requests
import time


# [ZH] 服务地址 — 指向 Module D 编排器
# [EN] Service URL — points to Module D orchestrator
PIPELINE_URL = os.getenv("PIPELINE_URL", "http://127.0.0.1:8082")

# [ZH] 重试设置 / [EN] Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # [ZH] 秒 / [EN] seconds


def _request_with_retry(method: str, url: str, payload: dict, timeout: int = 30) -> dict:
    """
    [ZH] 通用请求处理器，带重试逻辑和友好错误信息。
    [EN]
    Generic request handler with retry logic and detailed error messages.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            return {"status": "success", "data": response.json()}

        except requests.exceptions.ConnectionError:
            last_error = "connection_error"
            break

        except requests.exceptions.Timeout:
            last_error = "timeout"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            break

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            if status_code == 429:
                last_error = "rate_limit"
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * 2)
                    continue
            elif status_code >= 500:
                last_error = "server_error"
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
            else:
                last_error = f"http_{status_code}"
            break

        except Exception as e:
            last_error = str(e)
            break

    # [ZH] 将错误类型映射为用户友好消息 / [EN] Map error types to user-friendly messages
    error_messages = {
        "connection_error": "无法连接服务器，使用演示数据 / Cannot reach the server — using demo data.",
        "timeout": "服务器响应超时，请重试 / Server took too long to respond. Please try again.",
        "rate_limit": "请求过于频繁，请稍后重试 / Too many requests. Please wait a moment.",
        "server_error": "服务器内部错误，请稍后重试 / Server error. Please try again later.",
    }

    friendly_msg = error_messages.get(
        last_error,
        f"发生未知错误 / An unexpected error occurred: {last_error}",
    )

    return {"status": "error", "error_type": last_error, "message": friendly_msg}


def run_pipeline(location: str, keywords: str, num_results: int, resume_text: str = "") -> dict:
    """
    [ZH] 向 Module D（LangGraph 编排器）发送统一请求。一次调用返回岗位、简历建议和面试题。
         服务不可用时回退到演示数据。
    [EN] Send a unified request to Module D (LangGraph orchestrator).
         Returns jobs, resume_tips, and interview_prep in one call.
         Falls back to mock data if the server is not available.
    """
    result = _request_with_retry(
        method="POST",
        url=f"{PIPELINE_URL}/api/v1/run_pipeline",
        payload={
            "location": location,
            "keywords": keywords,
            "num_results": num_results,
            "resume_text": resume_text,
        },
        timeout=180,
    )

    if result["status"] == "success":
        data = result["data"]
        return {
            "status": "success",
            "jobs": data.get("jobs", []),
            "resume_tips": data.get("resume_tips", []),
            "interview_prep": data.get("interview_prep", []),
            "errors": data.get("errors", []),
            "is_live": True,
        }

    # [ZH] 服务不可达时回退到演示数据 / [EN] Fall back to mock data if server is unreachable
    if result.get("error_type") == "connection_error":
        mock = _mock_pipeline_response(num_results)
        mock["is_live"] = False
        return mock

    return {
        "status": "error",
        "jobs": [],
        "resume_tips": [],
        "interview_prep": [],
        "errors": [],
        "message": result["message"],
        "is_live": False,
    }


# ==============================================
# [ZH] 开发用演示数据（API 上线后可移除）
# [EN] Mock data for development (remove when APIs are live)
# ==============================================

def _mock_pipeline_response(num_results: int) -> dict:
    mock_jobs = [
        {
            "company": "Wayfair",
            "job_title": "Data Science Intern",
            "estimated_salary": "$30 - $35/hr",
            "core_skills": ["Python", "SQL", "Machine Learning"],
            "summary": "Build ML models for product recommendation engine",
            "apply_link": "https://wayfair.com/careers",
        },
        {
            "company": "HubSpot",
            "job_title": "AI Research Intern",
            "estimated_salary": "$32 - $40/hr",
            "core_skills": ["Python", "NLP", "TensorFlow"],
            "summary": "Develop NLP features for marketing automation platform",
            "apply_link": "https://hubspot.com/careers",
        },
        {
            "company": "Toast",
            "job_title": "Data Engineer Intern",
            "estimated_salary": "$28 - $34/hr",
            "core_skills": ["Python", "Spark", "SQL", "AWS"],
            "summary": "Build data pipelines for restaurant analytics platform",
            "apply_link": "https://toast.com/careers",
        },
        {
            "company": "DraftKings",
            "job_title": "ML Engineer Intern",
            "estimated_salary": "$35 - $42/hr",
            "core_skills": ["Python", "PyTorch", "Docker"],
            "summary": "Create real-time prediction models for sports analytics",
            "apply_link": "https://draftkings.com/careers",
        },
        {
            "company": "Akamai",
            "job_title": "Data Analyst Intern",
            "estimated_salary": "$25 - $30/hr",
            "core_skills": ["SQL", "Tableau", "Python"],
            "summary": "Analyze network performance data and build dashboards",
            "apply_link": "https://akamai.com/careers",
        },
    ]

    mock_interview_prep = []
    for job in mock_jobs[:num_results]:
        mock_interview_prep.append({
            "status": "success",
            "company": job["company"],
            "job_title": job["job_title"],
            "candidate_highlights": ["Strong Python skills", "ML project experience"],
            "questions": [
                {
                    "category": "Technical",
                    "question": f"Tell me about a project where you used Python to solve a real data problem at {job['company']}.",
                    "rationale": "Assesses hands-on coding and problem-solving ability.",
                },
                {
                    "category": "Behavioral",
                    "question": f"How would you handle a disagreement with a teammate about a technical approach at {job['company']}?",
                    "rationale": "Evaluates collaboration and communication skills.",
                },
                {
                    "category": "Role-Specific",
                    "question": f"How would you design a data pipeline for {job['company']}'s platform?",
                    "rationale": "Tests domain knowledge relevant to the role.",
                },
            ],
        })

    return {
        "status": "success",
        "jobs": mock_jobs[:num_results],
        "resume_tips": [
            "Use the STAR method (Situation, Task, Action, Result) for behavioral questions.",
            "Highlight experience with AI/ML frameworks and cloud deployment.",
        ],
        "interview_prep": mock_interview_prep,
        "errors": [],
    }
