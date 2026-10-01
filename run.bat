@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM Standard RAG — One-Command Launcher (Windows)
REM ==============================================================================

echo ==================================================
echo   Starting Standard RAG Application (Windows)
echo ==================================================

cd /d "%~dp0"

REM 1. Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python 3 is not installed or not in PATH.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py -3
) else (
    set PYTHON_CMD=python
)

REM 2. Check Node & npm
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / npm is not installed or not in PATH.
    pause
    exit /b 1
)

REM 3. Setup Virtual Environment
if not exist ".venv" (
    echo [*] Creating Python virtual environment in .venv...
    %PYTHON_CMD% -m venv .venv
    echo [*] Installing backend dependencies...
    call .venv\Scripts\pip install --upgrade pip
    call .venv\Scripts\pip install -r requirements.txt
) else (
    .venv\Scripts\python -c "import fastapi, langchain, chromadb" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [*] Installing missing backend dependencies...
        call .venv\Scripts\pip install -r requirements.txt
    )
)

REM 4. Check .env configuration
if not exist ".env" (
    echo [!] No .env found. Copying from .env.example...
    copy .env.example .env
    echo [!] Please update .env with your GOOGLE_API_KEY!
)

REM 5. Setup Frontend
if not exist "frontend\node_modules" (
    echo [*] Installing frontend npm dependencies...
    cd frontend
    call npm install
    cd ..
)

echo ==================================================
echo   Launching Backend and Frontend...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ==================================================

REM Start Backend in separate background window
start "Standard RAG Backend" cmd /k "call .venv\Scripts\activate.bat && uvicorn backend.app:app --host 0.0.0.0 --port 8000"

REM Wait 2 seconds for backend to initialize
timeout /t 2 /nobreak >nul

REM Start Frontend in current window
cd frontend
call npm run dev -- --port 5173

pause
