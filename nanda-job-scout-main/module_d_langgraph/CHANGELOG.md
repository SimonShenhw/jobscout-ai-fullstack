# CHANGELOG — Module D Integration & Bug Fixes
> Generated: 2026-03-25 | For traceability of all changes made during Module D integration.

---

## [NEW] `module_d_langgraph/master_graph.py`
**Purpose**: LangGraph StateGraph orchestrator connecting all three services.

- Created `PipelineState` (TypedDict) to carry data between graph nodes
- 4 graph nodes: `scout_jobs` → `retrieve_tips` → `generate_questions` → `merge_results`
- Each node calls its respective service via `httpx.AsyncClient`
- Error isolation: individual node failures are captured in `errors[]` without killing the pipeline
- FastAPI server on **port 8082** with endpoints:
  - `POST /api/v1/run_pipeline` — runs the full pipeline
  - `GET /health` — health check
- Service URLs configurable via env vars: `AGENT1_URL`, `MODULE_A_URL`, `AGENT2_URL`

---

## [NEW] `module_d_langgraph/requirements.txt`
**Purpose**: Dependencies for Module D.

- `langgraph>=0.2.0`, `langchain-core>=0.2.0`
- `httpx>=0.27.0` (async HTTP client)
- `fastapi>=0.111.0`, `uvicorn[standard]>=0.29.0`
- `pydantic>=2.7.0`

---

## [MODIFIED] `agent2_questions/workflow.py`
**Bug fixes and new endpoint.**

### Change 1: Added `estimated_salary` field to `JobJD`
```diff
 class JobJD(BaseModel):
-    """Mirrors Agent 1's JobJD — no changes needed for A2A compatibility."""
+    """Mirrors Agent 1's JobJD — aligned with Agent 1 schema for A2A compatibility."""
     company: str
     job_title: str
+    estimated_salary: str = Field(default="Not Specified", description="Estimated salary or 'Not Specified'")
     core_skills: List[str]
```
**Reason**: Agent 1's `JobJD` includes `estimated_salary`, but Agent 2's did not. This caused a schema mismatch in the A2A protocol. Default value ensures backward compatibility.

### Change 2: Added `POST /api/v1/prep_json` endpoint
- New Pydantic model `PrepJsonRequest` with `jobs: List[dict]` and `resume_text: str`
- New endpoint accepts JSON body (no file upload required)
- Used by Module D and the frontend
- Original multipart `/api/v1/prep` endpoint remains unchanged

### Change 3: Version bumped to `1.1.0`

---

## [MODIFIED] `frontend_ui/api_client.py`
**Fixed API call format to match Agent 2.**

### Change: `generate_interview_questions()` function
```diff
-    url="http://127.0.0.1:8081/api/v1/prep",
-    payload={"job": job, "resume_text": resume_text},
+    url="http://127.0.0.1:8081/api/v1/prep_json",
+    payload={"jobs": [job], "resume_text": resume_text},
```
**Reason**: The frontend was sending a JSON body to an endpoint that expected multipart form data. This would cause a 422 Unprocessable Entity error. Changed to call the new `/api/v1/prep_json` endpoint with the correct payload structure.

Also updated response parsing to extract questions from the batch response format (`results[].questions[].question`).

---

## [MODIFIED] `run_all.bat`
**Added Module D to the startup sequence.**

- Added `pip install -r module_d_langgraph\requirements.txt`
- Added `start "Module D - LangGraph"` command (port 8082)

---

## Service Port Map

| Service | Port | Endpoint |
|---------|------|----------|
| Agent 1 (Job Scout) | 8080 | `POST /api/v1/scout` |
| Module A (VectorDB) | 8000 | `POST /api/v1/search` |
| Agent 2 (Interview Prep) | 8081 | `POST /api/v1/prep` (multipart) / `POST /api/v1/prep_json` (JSON) |
| **Module D (LangGraph)** | **8082** | `POST /api/v1/run_pipeline` |
