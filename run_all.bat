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
echo [1/6] Starting Agent 1 (Job Scout) on port 8080...
start "Agent 1 - Scout" cmd /k "cd /d %~dp0agent1_scout && set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set SERPAPI_API_KEY=%SERPAPI_API_KEY% && python main.py"

echo [2/6] Starting Agent 2 (Interview Prep) on port 8081...
start "Agent 2 - Questions" cmd /k "cd /d %~dp0agent2_questions && set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set SERPAPI_API_KEY=%SERPAPI_API_KEY% && python workflow.py"

echo [3/6] Starting Agent B (Cost of Living) on port 8083...
start "Agent B - Cost" cmd /k "cd /d %~dp0agent_b_cost && set GOOGLE_API_KEY=%GOOGLE_API_KEY% && python main.py"

echo [4/6] Starting Module A (VectorDB) on port 8000...
start "Module A - VectorDB" cmd /k "cd /d %~dp0module_a_vectordb && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [5/6] Starting Module D (LangGraph Orchestrator) on port 8082...
start "Module D - LangGraph" cmd /k "cd /d %~dp0module_d_langgraph && set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set SERPAPI_API_KEY=%SERPAPI_API_KEY% && python master_graph.py"

:: Poll backends until ready (up to 90s for Module A which loads ML model)
echo.
echo Waiting for backends to start (polling /health endpoints)...
call :wait_for_health 8080 "Agent 1"
call :wait_for_health 8081 "Agent 2"
call :wait_for_health 8083 "Agent B"
call :wait_for_health 8000 "Module A"
call :wait_for_health 8082 "Module D"

echo [6/6] Starting Frontend UI on port 8501...
start "Frontend UI" cmd /k "cd /d %~dp0frontend_ui && python -m streamlit run app.py --server.port 8501"

echo.
echo ============================================
echo   All services started! (6 services)
echo   Open http://localhost:8501 in your browser
echo ============================================
echo.
echo Press any key to STOP all services and exit...
pause >nul

echo.
echo Stopping all services...

:: Kill by window title first (closes the cmd windows)
taskkill /FI "WINDOWTITLE eq Agent 1 - Scout*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Agent 2 - Questions*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Agent B - Cost*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Module A - VectorDB*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Module D - LangGraph*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend UI*" /F >nul 2>&1

:: Then kill any remaining processes by port (catches orphaned processes)
for %%P in (8080 8081 8083 8000 8082 8501) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%A >nul 2>&1
    )
)

echo [OK] All services stopped.
goto :eof

:: =====================================================
:: [ZH] 健康检查轮询函数 / [EN] Health check polling function
:: Usage: call :wait_for_health <port> <service_name>
:: =====================================================
:wait_for_health
set "PORT=%~1"
set "NAME=%~2"
set /a "ATTEMPTS=0"
:wait_loop
set /a "ATTEMPTS+=1"
if %ATTEMPTS% GTR 45 (
    echo   [WARN] %NAME% on port %PORT% not responding after 90s, continuing anyway...
    goto :eof
)
powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost:%PORT%/health' -TimeoutSec 2 -UseBasicParsing).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_loop
)
echo   [OK] %NAME% ready on port %PORT%.
goto :eof
