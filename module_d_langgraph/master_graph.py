"""
Module D — LangGraph Master Orchestrator (master_graph.py)
==========================================================
Uses LangGraph StateGraph to route data between:
  - Agent 1 (Job Scout,      port 8080)
  - Module A (VectorDB Tips, port 8000)
  - Agent 2 (Interview Prep, port 8081)

Exposes its own FastAPI server on port 8082.

[ZH] 使用 LangGraph 状态图将 Agent 1、Module A、Agent 2 串联为完整流水线。
[EN] Uses LangGraph StateGraph to chain Agent 1, Module A, Agent 2 into a full pipeline.
"""

import os
import sys
import json
import asyncio
import logging
from typing import List, Optional, TypedDict, Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

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
# 1. Service URLs (configurable via env vars)
# ==================================================
AGENT1_URL = os.getenv("AGENT1_URL", "http://127.0.0.1:8080")
MODULE_A_URL = os.getenv("MODULE_A_URL", "http://127.0.0.1:8000")
AGENT2_URL = os.getenv("AGENT2_URL", "http://127.0.0.1:8081")


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
        async with httpx.AsyncClient(timeout=90.0) as client:
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
        async with httpx.AsyncClient(timeout=30.0) as client:
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
        async with httpx.AsyncClient(timeout=120.0) as client:
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
    [ZH] 构建 LangGraph 状态图：scout → [tips + questions 并行] → merge → END
    [EN] Build LangGraph state graph: scout → [tips + questions parallel] → merge → END
    """
    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("scout_jobs", scout_jobs)
    graph.add_node("retrieve_tips", retrieve_tips)
    graph.add_node("generate_questions", generate_questions)
    graph.add_node("merge_results", merge_results)

    # scout_jobs runs first, then retrieve_tips and generate_questions run in PARALLEL,
    # both fan-in to merge_results before reaching END.
    graph.set_entry_point("scout_jobs")
    graph.add_edge("scout_jobs", "retrieve_tips")
    graph.add_edge("scout_jobs", "generate_questions")
    graph.add_edge("retrieve_tips", "merge_results")
    graph.add_edge("generate_questions", "merge_results")
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
async def run_pipeline(request: PipelineRequest):
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
            errors=final_state.get("errors", []),
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
