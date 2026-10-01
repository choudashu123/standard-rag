#!/usr/bin/env bash
set -e

# ==============================================================================
# Standard RAG — One-Command Launcher (macOS & Linux)
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "=================================================="
echo "⚡ Starting Standard RAG Application"
echo "=================================================="

# 1. Check Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
else
    echo "❌ Error: Python 3 is not installed or not in PATH."
    exit 1
fi

# 2. Check Node & npm
if ! command -v npm >/dev/null 2>&1; then
    echo "❌ Error: Node.js / npm is not installed or not in PATH."
    exit 1
fi

# 3. Check / Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment in .venv..."
    $PYTHON_CMD -m venv .venv
    echo "📦 Installing Python dependencies from requirements.txt..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
else
    # Quick check if dependencies are installed
    if ! .venv/bin/python -c "import fastapi, langchain, chromadb" >/dev/null 2>&1; then
        echo "📦 Installing missing Python dependencies..."
        .venv/bin/pip install -r requirements.txt
    fi
fi

# 4. Check .env configuration
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating one from .env.example..."
    cp .env.example .env
    echo "👉 Please set your GOOGLE_API_KEY in the .env file if you haven't already!"
fi

# 5. Check / Install Frontend Dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend npm dependencies..."
    (cd frontend && npm install)
fi

# 6. Setup cleanup trap on exit
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "🛑 Shutting down Standard RAG..."
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    exit 0
}

trap cleanup INT TERM EXIT

# 7. Start Backend Server
echo "🚀 Starting Backend API on http://localhost:8000..."
.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 2

# 8. Start Frontend Dev Server
echo "✨ Starting Frontend UI on http://localhost:5173..."
cd frontend
npm run dev -- --port 5173 &
FRONTEND_PID=$!
cd "$ROOT_DIR"

echo "=================================================="
echo "✅ Standard RAG is running!"
echo "   • Frontend: http://localhost:5173"
echo "   • Backend:  http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop both servers."
echo "=================================================="

wait
