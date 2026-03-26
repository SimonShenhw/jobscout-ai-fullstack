@echo off
echo ============================================
echo   Job Scout AI — Starting All Services
echo ============================================

:: API Keys — loaded from .env file (never hardcode keys here)
if exist "%~dp0.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%~dp0.env") do set "%%A=%%B"
) else (
    echo [ERROR] .env file not found! Please create .env with GOOGLE_API_KEY and SERPAPI_API_KEY.
    pause
    exit /b 1
)

echo.
echo [1/5] Starting Agent 1 (Job Scout) on port 8080...
start "Agent 1 - Scout" cmd /k "cd /d %~dp0agent1_scout && set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set SERPAPI_API_KEY=%SERPAPI_API_KEY% && python main.py"

echo [2/5] Starting Agent 2 (Interview Prep) on port 8081...
start "Agent 2 - Questions" cmd /k "cd /d %~dp0agent2_questions && set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set SERPAPI_API_KEY=%SERPAPI_API_KEY% && python workflow.py"

echo [3/5] Starting Module A (VectorDB) on port 8000...
start "Module A - VectorDB" cmd /k "cd /d %~dp0module_a_vectordb && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [4/5] Starting Module D (LangGraph Orchestrator) on port 8082...
start "Module D - LangGraph" cmd /k "cd /d %~dp0module_d_langgraph && set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set SERPAPI_API_KEY=%SERPAPI_API_KEY% && python master_graph.py"

:: Wait for backends to initialize
echo.
echo Waiting for backends to start...
timeout /t 8 /nobreak >nul

echo [5/5] Starting Frontend UI on port 8501...
start "Frontend UI" cmd /k "cd /d %~dp0frontend_ui && python -m streamlit run app.py --server.port 8501"

echo.
echo ============================================
echo   All services started!
echo   Open http://localhost:8501 in your browser
echo ============================================
echo.
echo Press any key to close this window...
pause >nul
