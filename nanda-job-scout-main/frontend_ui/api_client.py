import os
import requests
import time


# Service URL — points to Module D orchestrator
PIPELINE_URL = os.getenv("PIPELINE_URL", "http://127.0.0.1:8082")

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def _request_with_retry(method: str, url: str, payload: dict, timeout: int = 30) -> dict:
    """
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

    error_messages = {
        "connection_error": "Cannot reach the server. It may not be deployed yet — using demo data.",
        "timeout": "Server took too long to respond. Please try again.",
        "rate_limit": "Too many requests. Please wait a moment and try again.",
        "server_error": "The server encountered an error. Please try again later.",
    }

    friendly_msg = error_messages.get(
        last_error,
        f"An unexpected error occurred: {last_error}",
    )

    return {"status": "error", "error_type": last_error, "message": friendly_msg}


def run_pipeline(location: str, keywords: str, num_results: int, resume_text: str = "") -> dict:
    """
    Send a unified request to Module D (LangGraph orchestrator).
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

    # Fall back to mock data if server is unreachable
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
# Mock data for development (remove when APIs are live)
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
