# Job Scout AI

AI-powered job search and interview preparation platform built with an **Agent-to-Agent (A2A)** architecture. The system chains multiple specialized agents through a LangGraph orchestrator to deliver end-to-end job discovery and personalized interview coaching.

## Architecture

```
Frontend (Streamlit)
    │
    ▼
Module D (LangGraph Orchestrator)
    │
    ├──► Agent 1 (Job Scout)        — SerpAPI + Gemini LLM
    ├──► Module A (Vector DB)       — Resume tips via ChromaDB
    └──► Agent 2 (Interview Prep)   — Gemini LLM question generation
```

Module D orchestrates the full pipeline: **Agent 1** and **Module A / Agent 2** run in parallel after the job search completes, minimizing total latency.

| Service | Port | Description |
|---------|------|-------------|
| Agent 1 | 8080 | Searches jobs via SerpAPI, structures results with Gemini |
| Agent 2 | 8081 | Generates tailored interview questions per job + resume |
| Module A | 8000 | Vector database for resume tips (ChromaDB + SentenceTransformers) |
| Module D | 8082 | LangGraph StateGraph orchestrator, chains all agents |
| Frontend | 8501 | Streamlit web UI with job cards, salary display, interview chat |

## Features

- **Job Search** — Real-time web search with structured extraction (title, company, salary, skills, apply link)
- **Interview Prep** — 3 tailored questions per job (Technical / Behavioral / Role-Specific) with rationale
- **Resume Tips** — Vector similarity search against curated tips database
- **Resume Upload** — PDF/TXT parsing for personalized question generation
- **Caching** — 10-min TTL cache on Agent 1 to save API quota on repeated searches
- **Demo Mode** — Frontend falls back to mock data when backends are unavailable

## Quick Start

### Prerequisites

- Python 3.11+
- API keys: `GOOGLE_API_KEY` (Gemini) and `SERPAPI_API_KEY`

### Option 1: Local (Windows)

1. Create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your_google_api_key
   SERPAPI_API_KEY=your_serpapi_key
   ```

2. Install dependencies:
   ```bash
   pip install -r frontend_ui/requirements.txt
   pip install -r agent1_scout/requirements.txt
   pip install -r agent2_questions/requirements.txt
   pip install -r module_d_langgraph/requirements.txt
   pip install sentence-transformers chromadb langchain
   ```

3. Build the vector database (first time only):
   ```bash
   cd module_a_vectordb
   python build_db.py
   ```

4. Double-click `run_all.bat` or start services manually:
   ```bash
   cd agent1_scout && python main.py        # port 8080
   cd agent2_questions && python workflow.py # port 8081
   cd module_a_vectordb && uvicorn main:app --port 8000
   cd module_d_langgraph && python master_graph.py  # port 8082
   cd frontend_ui && streamlit run app.py   # port 8501
   ```

5. Open http://localhost:8501

### Option 2: Docker Compose

1. Create a `.env` file in the project root (same as above).

2. Build and start all services:
   ```bash
   docker-compose up --build
   ```

3. Open http://localhost:8501

### Run Agent 1 Standalone

Agent 1 can be independently deployed and demonstrated:

```bash
cd agent1_scout
# Create .env with GOOGLE_API_KEY and SERPAPI_API_KEY
docker-compose up --build
```

Test it directly:
```bash
curl -X POST http://localhost:8080/api/v1/scout \
  -H "Content-Type: application/json" \
  -d '{"keywords": "AI Intern", "location": "Boston", "num_results": 2}'
```

## API Endpoints

### Agent 1 — Job Scout
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/scout` | Search and structure job listings |
| GET | `/health` | Health check |

### Agent 2 — Interview Prep
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/prep_json` | Generate interview questions (JSON body) |
| POST | `/api/v1/prep` | Generate interview questions (multipart form) |
| GET | `/health` | Health check |

### Module A — Vector DB
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/search` | Semantic search for resume tips |

### Module D — Orchestrator
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/run_pipeline` | Run full pipeline (jobs + tips + questions) |
| GET | `/health` | Health check |

## Tech Stack

- **LLM**: Google Gemini (gemini-3-flash-preview / gemini-2.5-flash)
- **Search**: SerpAPI
- **Orchestration**: LangGraph StateGraph
- **Vector DB**: ChromaDB + SentenceTransformers (all-MiniLM-L6-v2)
- **Backend**: FastAPI + Uvicorn
- **Frontend**: Streamlit
- **Containerization**: Docker Compose

## Project Structure

```
├── agent1_scout/           # Agent 1: Job search
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml  # Standalone deployment
├── agent2_questions/       # Agent 2: Interview prep
│   ├── workflow.py
│   ├── requirements.txt
│   └── Dockerfile
├── module_a_vectordb/      # Module A: Resume tips vector DB
│   ├── main.py
│   ├── build_db.py
│   ├── resume_tips.txt
│   └── Dockerfile
├── module_d_langgraph/     # Module D: LangGraph orchestrator
│   ├── master_graph.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend_ui/            # Streamlit web UI
│   ├── app.py
│   ├── api_client.py
│   ├── style.css
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml      # Full-stack orchestration
├── run_all.bat             # Windows one-click launcher
└── .env                    # API keys (not tracked by git)
```

## Team

AAI 5025 Group Project
