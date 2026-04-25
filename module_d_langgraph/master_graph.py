"""
Module D — LangGraph Master Orchestrator (master_graph.py)
==========================================================
Uses LangGraph StateGraph to route data between:
  - Agent 1 (Job Scout,      port 8080)
  - Module A (VectorDB Tips, port 8000)
  - Agent 2 (Interview Prep, port 8081)
  - Agent B (Cost of Living, port 8083)

Exposes its own FastAPI server on port 8082.

[ZH] 使用 LangGraph 状态图将 Agent 1、Module A、Agent 2、Agent B 串联为完整流水线。
[EN] Uses LangGraph StateGraph to chain Agent 1, Module A, Agent 2, Agent B into a full pipeline.
"""

import os
import sys
import json
import uuid
import asyncio
import logging
from typing import List, Optional, TypedDict, Any

import httpx
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from langgraph.graph import StateGraph, END
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ── Encoding fix for Windows cmd ──
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("module_d")


# ==================================================
# 1. 集中式配置（Pydantic Settings）
# 1. Centralized Settings (Pydantic Settings)
# ==================================================

class Settings(BaseSettings):
    """[ZH] 集中管理所有配置项 / [EN] Centralized application settings."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # [ZH] 服务地址 / [EN] Service URLs
    agent1_url: str = "http://127.0.0.1:8080"
    module_a_url: str = "http://127.0.0.1:8000"
    agent2_url: str = "http://127.0.0.1:8081"
    agent_b_url: str = "http://127.0.0.1:8083"

    # [ZH] 安全 / [EN] Security
    api_key: str = ""
    allowed_origins: str = "*"
    rate_limit: str = "10/minute"

    # [ZH] LLM / [EN] LLM
    gemini_model: str = "gemini-2.5-flash"

    # [ZH] 超时（秒）/ [EN] Timeouts (seconds)
    agent1_timeout: float = 90.0
    module_a_timeout: float = 30.0
    agent2_timeout: float = 120.0
    agent_b_timeout: float = 60.0


settings = Settings()
AGENT1_URL = settings.agent1_url
MODULE_A_URL = settings.module_a_url
AGENT2_URL = settings.agent2_url
AGENT_B_URL = settings.agent_b_url


# ==================================================
# 2. Pydantic Models — API Request / Response
# ==================================================

class PipelineRequest(BaseModel):
    """[ZH] 前端或测试脚本发来的统一请求 / [EN] Unified request from frontend or test scripts."""
    keywords: str = Field(default="Data Scientist AI Intern", description="Search keywords")
    location: str = Field(default="Greater Boston Area", description="Search location")
    num_results: int = Field(default=3, ge=1, le=10, description="Number of jobs to return")
    resume_text: str = Field(default="", description="Plain-text resume content")


class PipelineResponse(BaseModel):
    """[ZH] 流水线最终返回的完整结果 / [EN] Full pipeline result returned to the caller."""
    status: str
    jobs: list = Field(default_factory=list)
    resume_tips: list = Field(default_factory=list)
    interview_prep: list = Field(default_factory=list)
    cost_of_living: list = Field(default_factory=list, description="[ZH] Agent B 生活成本评估 / [EN] Agent B cost of living evaluations")
    errors: list = Field(default_factory=list, description="Non-fatal errors encountered during pipeline")


# ==================================================
# 3. LangGraph State Definition
# ==================================================

class PipelineState(TypedDict):
    """
    [ZH] 在图节点之间传递的共享状态。
    [EN] Shared state passed between graph nodes.
    """
    # Inputs
    keywords: str
    location: str
    num_results: int
    resume_text: str
    # Intermediate / outputs
    jobs: list
    resume_tips: list
    interview_prep: list
    cost_of_living: list
    errors: list


# ==================================================
# 4. Graph Node Functions
# ==================================================

async def scout_jobs(state: PipelineState) -> dict:
    """
    Node 1: Call Agent 1 to search for jobs.
    [ZH] 节点 1：调用 Agent 1 搜索岗位。
    """
    logger.info("[Node: scout_jobs] Calling Agent 1...")
    try:
        async with httpx.AsyncClient(timeout=settings.agent1_timeout) as client:
            resp = await client.post(
                f"{AGENT1_URL}/api/v1/scout",
                json={
                    "location": state["location"],
                    "keywords": state["keywords"],
                    "num_results": state["num_results"],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("jobs", [])
            logger.info(f"[Node: scout_jobs] Received {len(jobs)} jobs from Agent 1.")
            return {"jobs": jobs}
    except Exception as e:
        error_msg = f"Agent 1 (scout_jobs) failed: {e}"
        logger.error(error_msg)
        return {"jobs": [], "errors": state.get("errors", []) + [error_msg]}


async def retrieve_tips(state: PipelineState) -> dict:
    """
    Node 2: Call Module A to retrieve resume tips based on job skills.
    [ZH] 节点 2：调用 Module A 根据岗位技能检索简历建议。
    """
    logger.info("[Node: retrieve_tips] Calling Module A...")

    # Build a query from the job skills discovered by Agent 1
    all_skills = []
    for job in state.get("jobs", []):
        all_skills.extend(job.get("core_skills", []))

    if not all_skills:
        query = "tech resume tips for software engineering internships"
    else:
        unique_skills = list(set(all_skills))[:10]
        query = f"resume tips for {', '.join(unique_skills)} roles"

    try:
        async with httpx.AsyncClient(timeout=settings.module_a_timeout) as client:
            resp = await client.post(
                f"{MODULE_A_URL}/api/v1/search",
                json={"query": query},
            )
            resp.raise_for_status()
            data = resp.json()
            tips = data.get("result", "")
            tips_list = [t.strip() for t in tips.split("\n\n") if t.strip()] if isinstance(tips, str) else [tips]
            logger.info(f"[Node: retrieve_tips] Received {len(tips_list)} tips from Module A.")
            return {"resume_tips": tips_list}
    except Exception as e:
        error_msg = f"Module A (retrieve_tips) failed: {e}"
        logger.error(error_msg)
        return {"resume_tips": [], "errors": state.get("errors", []) + [error_msg]}


async def generate_questions(state: PipelineState) -> dict:
    """
    Node 3: Call Agent 2 to generate interview questions.
    [ZH] 节点 3：调用 Agent 2 生成面试题。
    """
    logger.info("[Node: generate_questions] Calling Agent 2...")

    jobs = state.get("jobs", [])
    resume_text = state.get("resume_text", "")

    if not jobs:
        logger.warning("[Node: generate_questions] No jobs to process, skipping.")
        return {"interview_prep": []}

    if not resume_text:
        resume_text = "No resume provided."

    try:
        async with httpx.AsyncClient(timeout=settings.agent2_timeout) as client:
            resp = await client.post(
                f"{AGENT2_URL}/api/v1/prep_json",
                json={
                    "jobs": jobs,
                    "resume_text": resume_text,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            logger.info(f"[Node: generate_questions] Received prep for {len(results)} jobs from Agent 2.")
            return {"interview_prep": results}
    except Exception as e:
        error_msg = f"Agent 2 (generate_questions) failed: {e}"
        logger.error(error_msg)
        return {"interview_prep": [], "errors": state.get("errors", []) + [error_msg]}


async def evaluate_cost(state: PipelineState) -> dict:
    """
    Node 4: Call Agent B to evaluate cost of living for each job (concurrent).
    [ZH] 节点 4：并发调用 Agent B 为每个岗位评估生活成本。
    """
    logger.info("[Node: evaluate_cost] Calling Agent B (concurrent)...")

    jobs = state.get("jobs", [])
    if not jobs:
        logger.warning("[Node: evaluate_cost] No jobs to evaluate, skipping.")
        return {"cost_of_living": []}

    location = state.get("location", "Boston")

    async def _eval_one(client: httpx.AsyncClient, job: dict) -> dict:
        """[ZH] 单个岗位评估 / [EN] Evaluate a single job."""
        try:
            resp = await client.post(
                f"{AGENT_B_URL}/api/v1/evaluate",
                json={
                    "job_title": job.get("job_title", ""),
                    "location": location,
                    "estimated_salary": job.get("estimated_salary", "Not Specified"),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "company": job.get("company", ""),
                "job_title": job.get("job_title", ""),
                "affordability": data.get("affordability", "Unknown"),
                "monthly_cost_range": data.get("monthly_cost_range", ""),
                "monthly_surplus_range": data.get("monthly_surplus_range", ""),
                "ai_comment": data.get("ai_comment", ""),
            }
        except Exception as e:
            logger.warning(f"[Node: evaluate_cost] Failed for {job.get('job_title', '?')}: {e}")
            return {
                "company": job.get("company", ""),
                "job_title": job.get("job_title", ""),
                "affordability": "Unavailable",
                "monthly_cost_range": "",
                "monthly_surplus_range": "",
                "ai_comment": "",
            }

    try:
        # [ZH] 并发执行所有岗位评估，3 个 job 从 ~6s 降到 ~2s
        # [EN] Run all evaluations concurrently — 3 jobs goes from ~6s to ~2s
        async with httpx.AsyncClient(timeout=settings.agent_b_timeout) as client:
            results = await asyncio.gather(*[_eval_one(client, job) for job in jobs])
        logger.info(f"[Node: evaluate_cost] Evaluated {len(results)} jobs via Agent B.")
        return {"cost_of_living": list(results)}
    except Exception as e:
        error_msg = f"Agent B (evaluate_cost) failed: {e}"
        logger.error(error_msg)
        return {"cost_of_living": [], "errors": state.get("errors", []) + [error_msg]}


async def merge_results(state: PipelineState) -> dict:
    """
    Node 4: Final merge — no-op, state already holds everything.
    [ZH] 节点 4：最终合并 — 状态中已包含所有数据。
    """
    logger.info("[Node: merge_results] Pipeline complete.")
    return {}


# ==================================================
# 5. Build the LangGraph StateGraph
# ==================================================

def build_graph() -> StateGraph:
    """
    [ZH] 构建 LangGraph 状态图：scout → [tips + questions + cost 并行] → merge → END
    [EN] Build LangGraph state graph: scout → [tips + questions + cost parallel] → merge → END
    """
    graph = StateGraph(PipelineState)

    # [ZH] 添加节点 / [EN] Add nodes
    graph.add_node("scout_jobs", scout_jobs)
    graph.add_node("retrieve_tips", retrieve_tips)
    graph.add_node("generate_questions", generate_questions)
    graph.add_node("evaluate_cost", evaluate_cost)
    graph.add_node("merge_results", merge_results)

    # [ZH] scout_jobs 先执行，然后 retrieve_tips、generate_questions、evaluate_cost 三者并行，
    #      全部完成后汇入 merge_results → END
    # [EN] scout_jobs runs first, then retrieve_tips, generate_questions, and evaluate_cost
    #      run in PARALLEL, all fan-in to merge_results before reaching END.
    graph.set_entry_point("scout_jobs")
    graph.add_edge("scout_jobs", "retrieve_tips")
    graph.add_edge("scout_jobs", "generate_questions")
    graph.add_edge("scout_jobs", "evaluate_cost")
    graph.add_edge("retrieve_tips", "merge_results")
    graph.add_edge("generate_questions", "merge_results")
    graph.add_edge("evaluate_cost", "merge_results")
    graph.add_edge("merge_results", END)

    return graph.compile()


# Module-level compiled graph (reused across requests)
pipeline = build_graph()


# ==================================================
# 6. FastAPI Deployment Shell (port 8082)
# ==================================================

app = FastAPI(
    title="Module D: LangGraph Pipeline Orchestrator",
    description=(
        "MIT NANDA Sandbox — Module D. "
        "Orchestrates Agent 1 (Job Scout), Module A (VectorDB), "
        "and Agent 2 (Interview Prep) via LangGraph StateGraph."
    ),
    version="1.0.0",
)

# [ZH] CORS 中间件 / [EN] CORS middleware
_origins = settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# [ZH] 请求 ID 中间件：每个请求生成唯一 ID，便于跨服务追踪
# [EN] Request ID middleware: assigns a unique ID per request for cross-service tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id
    logger.info(f"[req={request_id}] {request.method} {request.url.path}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# [ZH] 速率限制：基于 IP / [EN] Rate limiter: IP-based
_rate_limit = settings.rate_limit
limiter = Limiter(key_func=get_remote_address, default_limits=[_rate_limit])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# [ZH] API Key 鉴权依赖（环境变量 API_KEY 设置时启用）
# [EN] API key auth (enabled when API_KEY env var is set)
async def verify_api_key(x_api_key: str = Header(None)):
    expected = settings.api_key.strip()
    if not expected:
        return  # [ZH] 未设置则跳过 / [EN] Skip if not configured
    if not x_api_key or x_api_key.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


@app.get("/health", tags=["Ops"])
async def health():
    """[ZH] 健康检查 / [EN] Health check."""
    return {"status": "ok", "module": "langgraph-orchestrator", "version": "1.0.0"}


@app.post(
    "/api/v1/run_pipeline",
    response_model=PipelineResponse,
    tags=["Pipeline"],
    summary="Run the full job scout → resume tips → interview prep pipeline",
)
@limiter.limit(_rate_limit)
async def run_pipeline(request: PipelineRequest, http_request: Request, _: None = None):
    # [ZH] 鉴权（如果配置了 API_KEY）/ [EN] Verify API key if configured
    await verify_api_key(http_request.headers.get("x-api-key"))
    """
    [ZH] 执行完整流水线：搜索岗位 → 检索简历建议 → 生成面试题
    [EN] Execute the full pipeline: scout jobs → retrieve tips → generate questions
    """
    logger.info(f"Pipeline invoked: keywords='{request.keywords}', location='{request.location}'")

    initial_state: PipelineState = {
        "keywords": request.keywords,
        "location": request.location,
        "num_results": request.num_results,
        "resume_text": request.resume_text,
        "jobs": [],
        "resume_tips": [],
        "interview_prep": [],
        "cost_of_living": [],
        "errors": [],
    }

    try:
        # Run the LangGraph pipeline
        final_state = await pipeline.ainvoke(initial_state)

        return PipelineResponse(
            status="success",
            jobs=final_state.get("jobs", []),
            resume_tips=final_state.get("resume_tips", []),
            interview_prep=final_state.get("interview_prep", []),
            cost_of_living=final_state.get("cost_of_living", []),
            errors=final_state.get("errors", []),
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}") from e


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
