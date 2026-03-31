# Job Scout AI

[English](#english) | [中文](#中文)

---

## English

AI-powered job search and interview preparation platform built with an **Agent-to-Agent (A2A)** architecture. The system chains multiple specialized agents through a LangGraph orchestrator to deliver end-to-end job discovery and personalized interview coaching.

### Architecture

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

Module D orchestrates the full pipeline: **Agent 1** runs first, then **Module A** and **Agent 2** run in parallel, minimizing total latency.

| Service | Port | Description |
|---------|------|-------------|
| Agent 1 | 8080 | Searches jobs via SerpAPI, structures results with Gemini |
| Agent 2 | 8081 | Generates tailored interview questions per job + resume |
| Module A | 8000 | Vector database for resume tips (ChromaDB + SentenceTransformers) |
| Module D | 8082 | LangGraph StateGraph orchestrator, chains all agents |
| Frontend | 8501 | Streamlit web UI with job cards, salary display, interview chat |

### Features

- **Job Search** — Real-time web search with structured extraction (title, company, salary, skills, apply link)
- **Interview Prep** — 3 tailored questions per job (Technical / Behavioral / Role-Specific) with rationale
- **Resume Tips** — Vector similarity search against curated tips database
- **Resume Upload** — PDF/TXT parsing for personalized question generation
- **Caching** — 10-min TTL cache on Agent 1 to save API quota on repeated searches
- **Demo Mode** — Frontend falls back to mock data when backends are unavailable

### Quick Start

#### Prerequisites

- Python 3.11+
- API keys: `GOOGLE_API_KEY` (Gemini) and `SERPAPI_API_KEY`

#### Option 1: Local (Windows)

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
   pip install sentence-transformers chromadb langchain langchain-huggingface langchain-chroma
   ```

3. Build the vector database (first time only):
   ```bash
   cd module_a_vectordb
   python build_db.py
   ```

4. (Windows + Python 3.14 only) Fix aiohttp DNS issue:
   ```bash
   pip uninstall aiodns -y
   ```

5. Double-click `run_all.bat` or start services manually:
   ```bash
   cd agent1_scout && python main.py        # port 8080
   cd agent2_questions && python workflow.py # port 8081
   cd module_a_vectordb && uvicorn main:app --port 8000
   cd module_d_langgraph && python master_graph.py  # port 8082
   cd frontend_ui && streamlit run app.py   # port 8501
   ```

6. Open http://localhost:8501

To stop all services, press any key in the `run_all.bat` window, or double-click `stop_all.bat`.

#### Option 2: Docker Compose

1. Create a `.env` file in the project root (same as above).

2. Build and start all services:
   ```bash
   docker-compose up --build
   ```

3. Open http://localhost:8501

#### Run Agent 1 Standalone

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

### API Endpoints

#### Agent 1 — Job Scout
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/scout` | Search and structure job listings |
| GET | `/health` | Health check |

#### Agent 2 — Interview Prep
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/prep_json` | Generate interview questions (JSON body) |
| POST | `/api/v1/prep` | Generate interview questions (multipart form) |
| GET | `/health` | Health check |

#### Module A — Vector DB
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/search` | Semantic search for resume tips |
| GET | `/health` | Health check |

#### Module D — Orchestrator
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/run_pipeline` | Run full pipeline (jobs + tips + questions) |
| GET | `/health` | Health check |

### Tech Stack

- **LLM**: Google Gemini (gemini-3-flash-preview / gemini-2.5-flash)
- **Search**: SerpAPI
- **Orchestration**: LangGraph StateGraph
- **Vector DB**: ChromaDB + SentenceTransformers (all-MiniLM-L6-v2)
- **Backend**: FastAPI + Uvicorn
- **Frontend**: Streamlit
- **Containerization**: Docker Compose

### Project Structure

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
├── run_all.bat             # Windows one-click launcher (press any key to stop all)
├── stop_all.bat            # Standalone service shutdown script
└── .env                    # API keys (not tracked by git)
```

### Team

AAI 5025 Group Project

---

## 中文

基于 **Agent-to-Agent (A2A)** 架构的 AI 求职搜索与面试准备平台。系统通过 LangGraph 编排器串联多个专业化 Agent，实现从岗位发现到个性化面试辅导的端到端流程。

### 系统架构

```
前端 (Streamlit)
    │
    ▼
Module D (LangGraph 编排器)
    │
    ├──► Agent 1 (岗位搜索)       — SerpAPI + Gemini LLM
    ├──► Module A (向量数据库)     — 基于 ChromaDB 的简历建议
    └──► Agent 2 (面试准备)       — Gemini LLM 生成面试题
```

Module D 编排完整流水线：**Agent 1** 先执行搜索，随后 **Module A** 和 **Agent 2** 并行执行，最大限度降低总延迟。

| 服务 | 端口 | 说明 |
|------|------|------|
| Agent 1 | 8080 | 通过 SerpAPI 搜索岗位，使用 Gemini 结构化解析结果 |
| Agent 2 | 8081 | 根据岗位 + 简历生成定制面试题 |
| Module A | 8000 | 简历建议向量数据库（ChromaDB + SentenceTransformers）|
| Module D | 8082 | LangGraph StateGraph 编排器，串联所有 Agent |
| 前端 | 8501 | Streamlit Web 界面，含岗位卡片、薪资显示、面试聊天 |

### 功能特性

- **岗位搜索** — 实时网络搜索 + 结构化提取（职位、公司、薪资、技能、申请链接）
- **面试准备** — 每个岗位生成 3 道定制面试题（技术 / 行为 / 岗位相关），附推荐理由
- **简历建议** — 基于向量相似度匹配的简历优化建议
- **简历上传** — 支持 PDF/TXT 解析，用于个性化面试题生成
- **缓存机制** — Agent 1 内置 10 分钟 TTL 缓存，节省 API 配额
- **演示模式** — 后端不可用时自动切换到演示数据

### 快速开始

#### 前置要求

- Python 3.11+
- API 密钥：`GOOGLE_API_KEY`（Gemini）和 `SERPAPI_API_KEY`

#### 方式一：本地运行（Windows）

1. 在项目根目录创建 `.env` 文件：
   ```
   GOOGLE_API_KEY=你的_google_api_key
   SERPAPI_API_KEY=你的_serpapi_key
   ```

2. 安装依赖：
   ```bash
   pip install -r frontend_ui/requirements.txt
   pip install -r agent1_scout/requirements.txt
   pip install -r agent2_questions/requirements.txt
   pip install -r module_d_langgraph/requirements.txt
   pip install sentence-transformers chromadb langchain langchain-huggingface langchain-chroma
   ```

3. 首次运行需构建向量数据库：
   ```bash
   cd module_a_vectordb
   python build_db.py
   ```

4. （仅 Windows + Python 3.14）修复 aiohttp DNS 问题：
   ```bash
   pip uninstall aiodns -y
   ```

5. 双击 `run_all.bat` 或手动启动各服务：
   ```bash
   cd agent1_scout && python main.py        # 端口 8080
   cd agent2_questions && python workflow.py # 端口 8081
   cd module_a_vectordb && uvicorn main:app --port 8000
   cd module_d_langgraph && python master_graph.py  # 端口 8082
   cd frontend_ui && streamlit run app.py   # 端口 8501
   ```

6. 打开 http://localhost:8501

关闭所有服务：在 `run_all.bat` 窗口按任意键，或双击 `stop_all.bat`。

#### 方式二：Docker Compose

1. 在项目根目录创建 `.env` 文件（同上）。

2. 构建并启动所有服务：
   ```bash
   docker-compose up --build
   ```

3. 打开 http://localhost:8501

#### 单独运行 Agent 1

Agent 1 支持独立部署和演示：

```bash
cd agent1_scout
# 创建 .env 文件，写入 GOOGLE_API_KEY 和 SERPAPI_API_KEY
docker-compose up --build
```

直接测试：
```bash
curl -X POST http://localhost:8080/api/v1/scout \
  -H "Content-Type: application/json" \
  -d '{"keywords": "AI Intern", "location": "Boston", "num_results": 2}'
```

### API 接口

#### Agent 1 — 岗位搜索
| 方法 | 接口 | 说明 |
|------|------|------|
| POST | `/api/v1/scout` | 搜索并结构化岗位列表 |
| GET | `/health` | 健康检查 |

#### Agent 2 — 面试准备
| 方法 | 接口 | 说明 |
|------|------|------|
| POST | `/api/v1/prep_json` | 生成面试题（JSON 格式）|
| POST | `/api/v1/prep` | 生成面试题（表单上传）|
| GET | `/health` | 健康检查 |

#### Module A — 向量数据库
| 方法 | 接口 | 说明 |
|------|------|------|
| POST | `/api/v1/search` | 语义搜索简历建议 |
| GET | `/health` | 健康检查 |

#### Module D — 编排器
| 方法 | 接口 | 说明 |
|------|------|------|
| POST | `/api/v1/run_pipeline` | 运行完整流水线（岗位 + 建议 + 面试题）|
| GET | `/health` | 健康检查 |

### 技术栈

- **大语言模型**：Google Gemini（gemini-3-flash-preview / gemini-2.5-flash）
- **搜索引擎**：SerpAPI
- **编排框架**：LangGraph StateGraph
- **向量数据库**：ChromaDB + SentenceTransformers（all-MiniLM-L6-v2）
- **后端框架**：FastAPI + Uvicorn
- **前端框架**：Streamlit
- **容器化**：Docker Compose

### 项目结构

```
├── agent1_scout/           # Agent 1：岗位搜索
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml  # 独立部署配置
├── agent2_questions/       # Agent 2：面试准备
│   ├── workflow.py
│   ├── requirements.txt
│   └── Dockerfile
├── module_a_vectordb/      # Module A：简历建议向量数据库
│   ├── main.py
│   ├── build_db.py
│   ├── resume_tips.txt
│   └── Dockerfile
├── module_d_langgraph/     # Module D：LangGraph 编排器
│   ├── master_graph.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend_ui/            # Streamlit Web 界面
│   ├── app.py
│   ├── api_client.py
│   ├── style.css
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml      # 全栈编排配置
├── run_all.bat             # Windows 一键启动（按任意键关闭所有服务）
├── stop_all.bat            # 独立服务关闭脚本
└── .env                    # API 密钥（不纳入 Git 追踪）
```

### 团队

AAI 5025 课程小组项目
