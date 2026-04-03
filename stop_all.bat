@echo off
echo ============================================
echo   Job Scout AI — Stopping All Services
echo ============================================
echo.

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

echo.
echo [OK] All services stopped.
echo.
pause
