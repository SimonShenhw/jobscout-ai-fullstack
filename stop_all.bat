@echo off
echo ============================================
echo   Job Scout AI — Stopping All Services
echo ============================================
echo.

:: Kill all service windows by their window titles (set in run_all.bat)
taskkill /FI "WINDOWTITLE eq Agent 1 - Scout*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Agent 2 - Questions*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Module A - VectorDB*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Module D - LangGraph*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend UI*" /F >nul 2>&1

echo.
echo [OK] All services stopped.
echo.
pause
