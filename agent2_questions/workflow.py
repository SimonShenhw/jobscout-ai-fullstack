import os
import sys
import json
import asyncio
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional

# [ZH] 简历解析依赖
# [EN] Resume parsing dependencies
import pdfplumber                          # pip install pdfplumber
from docx import Document as DocxDocument  # pip install python-docx
import io

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# [ZH] 修复 Windows cmd 打印非 ASCII 字符导致 GBK 编码崩溃
# [EN] Fix GBK encoding crash when printing non-ASCII chars in Windows cmd
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# [ZH] 配置日志格式
# [EN] Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agent2")


# ==========================================
# 1. 数据结构 (A2A 通信协议)
# 1. Data Structures (A2A Protocol)
#    [ZH] 与 Agent 1 的 ScoutResponse 模式对齐，实现 JSON 直传
#    [EN] Mirrors Agent 1's ScoutResponse schema for seamless A2A communication
# ==========================================

class JobJD(BaseModel):
    """Mirrors Agent 1's JobJD — aligned with Agent 1 schema for A2A compatibility."""
    company: str
    job_title: str
    estimated_salary: str = Field(default="Not Specified", description="Estimated salary or 'Not Specified'")
    core_skills: List[str]
    summary: str
    apply_link: str


class InterviewQuestion(BaseModel):
    category: str = Field(description="Question category: Technical | Behavioral | Role-Specific")
    question: str = Field(description="The tailored interview question")
    rationale: str = Field(description="Why this question was chosen given the resume and JD")


class InterviewPrepResponse(BaseModel):
    status: str
    company: str
    job_title: str
    candidate_highlights: List[str] = Field(description="Key resume strengths relevant to this JD")
    questions: List[InterviewQuestion]


class BatchInterviewPrepResponse(BaseModel):
    status: str
    results: List[InterviewPrepResponse]


# ==========================================
# 2. 简历解析工具
# 2. Resume Parsing Utilities
#    [ZH] 支持 .pdf、.docx 和 .txt 格式
#    [EN] Supports .pdf, .docx, and .txt formats
# ==========================================

def _parse_pdf(data: bytes) -> str:
    """[ZH] 使用 pdfplumber 从 PDF 提取纯文本 / [EN] Extract plain text from a PDF file using pdfplumber."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def _parse_docx(data: bytes) -> str:
    """[ZH] 从 .docx 文件提取纯文本 / [EN] Extract plain text from a .docx file."""
    doc = DocxDocument(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()


def _parse_txt(data: bytes) -> str:
    """[ZH] 解码纯文本简历，优先 UTF-8，回退 latin-1 / [EN] Decode a plain-text resume; try UTF-8, fall back to latin-1."""
    try:
        return data.decode("utf-8").strip()
    except UnicodeDecodeError:
        return data.decode("latin-1").strip()


def extract_resume_text(filename: str, data: bytes) -> str:
    """
    [ZH] 根据文件扩展名分派到对应解析器。不支持的格式抛出 ValueError。
    [EN] Dispatch to the correct parser based on file extension.
    Raises ValueError for unsupported formats so FastAPI can surface a clean 400.
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return _parse_pdf(data)
    elif ext == "docx":
        return _parse_docx(data)
    elif ext == "txt":
        return _parse_txt(data)
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Please upload a .pdf, .docx, or .txt file.")


# ==========================================
# 3. 模块级 LLM + Prompt（初始化一次，复用于所有请求）
# 3. Module-Level LLM + Prompt (initialized once, reused across requests)
# ==========================================

LLM = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert technical recruiter and career coach.
Given a candidate's resume and a specific job description, your task is:
1. Identify the candidate's most relevant skills and experiences (candidate_highlights).
2. Generate exactly 3 interview questions — one Technical, one Behavioral, one Role-Specific.
   Each question must be tailored to BOTH the JD and the candidate's actual background.
3. For each question, include a short rationale explaining why it's relevant.

Be specific. Reference actual skills, projects, or experiences from the resume where possible.
If any field in the JD is 'Not Available', infer reasonable context from the rest."""
    ),
    (
        "human",
        """=== JOB DESCRIPTION ===
Company:     {company}
Role:        {job_title}
Core Skills: {core_skills}
Summary:     {summary}

=== CANDIDATE RESUME ===
{resume}

Generate the structured output now."""
    ),
])

CHAIN = PROMPT | LLM.with_structured_output(InterviewPrepResponse)


# ==========================================
# 4. 核心 Agent 逻辑（每个岗位一个协程，asyncio.gather 并发执行）
# 4. Core Agent Logic (one coroutine per job, concurrent via asyncio.gather)
# ==========================================

async def generate_questions_for_job(
    job: JobJD,
    resume_text: str,
) -> InterviewPrepResponse:
    """
    [ZH] 为单个岗位生成 3 道定制面试题。LLM 解析失败最多重试 3 次。
    [EN] Generate 3 tailored interview questions for a single job.
    Retries up to 3 times on LLM parse failure (mirrors Agent 1's pattern).
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result: InterviewPrepResponse = await CHAIN.ainvoke({
                "company":     job.company,
                "job_title":   job.job_title,
                "core_skills": ", ".join(job.core_skills),
                "summary":     job.summary,
                "resume":      resume_text,
            })
            return result
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} for '{job.job_title}' @ {job.company} failed: {e}")
            if attempt == max_retries - 1:
                raise Exception(
                    f"LLM failed to generate questions for {job.job_title} @ {job.company} after {max_retries} attempts."
                )
            await asyncio.sleep(1)


async def run_interview_agent(
    jobs: List[JobJD],
    resume_text: str,
) -> BatchInterviewPrepResponse:
    """
    [ZH] 入口：并发处理 Agent 1 输出的所有岗位。
    [EN] Entry point: concurrently processes every job from Agent 1's output.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("Missing GOOGLE_API_KEY environment variable.")

    # [ZH] 扇出：并发处理所有岗位 / [EN] Fan-out: run all jobs concurrently
    logger.info(f"Processing {len(jobs)} job(s) concurrently...")
    tasks = [generate_questions_for_job(job, resume_text) for job in jobs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # [ZH] 分离成功与失败 — 单个岗位失败不影响整批 / [EN] Separate successes from failures — never let one bad job kill the batch
    successful: List[InterviewPrepResponse] = []
    for job, result in zip(jobs, results):
        if isinstance(result, Exception):
            logger.error(f"Skipping '{job.job_title}' @ {job.company}: {result}")
        else:
            successful.append(result)

    if not successful:
        raise Exception("All jobs failed to generate interview questions. Check your LLM API key and quota.")

    return BatchInterviewPrepResponse(status="success", results=successful)


# ==========================================
# 5. 部署外壳 (FastAPI 封装)
# 5. Deployment Shell (FastAPI Wrapper)
# ==========================================

app = FastAPI(
    title="Interview Prep Agent API",
    description=(
        "MIT NANDA Sandbox — Agent 2. "
        "Ingests Agent 1's job JSON + a candidate resume, "
        "and returns 3 tailored interview questions per job."
    ),
    version="1.0.0",
)


@app.post(
    "/api/v1/prep",
    response_model=BatchInterviewPrepResponse,
    tags=["Interview Prep Agent"],
    summary="Generate tailored interview questions from Agent 1 output + resume",
)
async def api_generate_interview_questions(
    resume: UploadFile = File(
        ...,
        description="Candidate resume — accepts .pdf, .docx, or .txt"
    ),
    jobs_json: str = Form(
        ...,
        description=(
            "Agent 1's JSON output — either the full ScoutResponse object "
            "({status, jobs: [...]}) or just the jobs array ([...])."
        )
    ),
):
    # [ZH] 1. 解析简历 / [EN] 1. Parse resume
    try:
        resume_bytes = await resume.read()
        resume_text = extract_resume_text(resume.filename, resume_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {e}")

    if not resume_text:
        raise HTTPException(status_code=422, detail="Resume appears to be empty or unreadable.")

    # [ZH] 2. 解析 Agent 1 的 JSON（兼容完整对象或纯数组）/ [EN] 2. Parse Agent 1 JSON (flexible: full object OR bare array)
    try:
        parsed = json.loads(jobs_json)
        # Accept both {"status": ..., "jobs": [...]} and plain [...]
        raw_jobs = parsed.get("jobs", parsed) if isinstance(parsed, dict) else parsed
        jobs = [JobJD(**j) for j in raw_jobs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid jobs_json format: {e}")

    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs found in jobs_json.")

    # [ZH] 3. 运行 Agent / [EN] 3. Run the agent
    try:
        response = await run_interview_agent(jobs, resume_text)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 6. JSON 格式接口（供 Module D 和前端使用）
# 6. JSON-body Endpoint (for Module D / Frontend)
# ==========================================

class PrepJsonRequest(BaseModel):
    """JSON request body for the prep_json endpoint."""
    jobs: List[dict]
    resume_text: str = ""


@app.post(
    "/api/v1/prep_json",
    response_model=BatchInterviewPrepResponse,
    tags=["Interview Prep Agent"],
    summary="Generate interview questions from JSON body (no file upload)",
)
async def api_generate_interview_questions_json(request: PrepJsonRequest):
    """[ZH] JSON 格式接口，无需文件上传 / [EN] JSON endpoint, no file upload needed."""
    resume_text = request.resume_text or "No resume provided."

    try:
        jobs = [JobJD(**j) for j in request.jobs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid job format: {e}")

    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs provided.")

    try:
        response = await run_interview_agent(jobs, resume_text)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 7. 健康检查 / Health Check
# ==========================================

@app.get("/health", tags=["Ops"])
async def health():
    return {"status": "ok", "agent": "interview-prep", "version": "1.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)  # Port 8081 keeps it separate from Agent 1 (8080)
