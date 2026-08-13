@echo off
echo ============================================
echo    Excel to Markdown Converter
echo ============================================
echo.

cd /d "%~dp0"

set PORT=8001

echo [INFO] Starting FastAPI server on port %PORT%...
echo [INFO] Opening browser...
echo.

start powershell -NoExit -Command "cd '%~dp0'; uvicorn app.main:app --port %PORT% --reload"

timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:%PORT%"

exit