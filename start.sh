#!/usr/bin/env bash
# ==============================================================================
# Incident Response Agent - Localhost Setup & Runner Script
# Starts FastAPI backend (port 8000) and React Vite frontend (port 5173)
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=========================================================="
echo "🚀 Setting up & Starting Localhost Environment..."
echo "=========================================================="

# 1. Resolve Node & NPM
if ! command -v node >/dev/null 2>&1; then
    if [ -d "/Users/balaji/.nvm/versions/node" ]; then
        LATEST_NODE=$(ls -d /Users/balaji/.nvm/versions/node/* 2>/dev/null | tail -n 1)
        if [ -n "$LATEST_NODE" ]; then
            export PATH="$LATEST_NODE/bin:$PATH"
        fi
    fi
fi

if ! command -v node >/dev/null 2>&1; then
    echo "❌ Error: Node.js is not found in PATH. Please install Node.js (v18+)."
    exit 1
fi

echo " Node version: $(node -v)"

# 2. Resolve Python Virtual Environment
VENV_DIR="$DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment in ./venv..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    echo "📦 Installing Python dependencies..."
    "$VENV_DIR/bin/pip" install -r requirements.txt
else
    echo " Python virtual environment found: $VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python3"
UVICORN_BIN="$VENV_DIR/bin/uvicorn"

# 3. Ensure Frontend Dependencies
if [ ! -d "$DIR/frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies with npm..."
    (cd "$DIR/frontend" && npm install)
else
    echo " Frontend node_modules present."
fi

# 4. Check if ports are already running
BACKEND_PID=$(lsof -ti:8000 || true)
FRONTEND_PID=$(lsof -ti:5173 || true)

if [ -n "$BACKEND_PID" ]; then
    echo "ℹ️  Backend already listening on port 8000 (PID: $BACKEND_PID)"
fi

if [ -n "$FRONTEND_PID" ]; then
    echo "ℹ️  Frontend already listening on port 5173 (PID: $FRONTEND_PID)"
fi

if [ -n "$BACKEND_PID" ] && [ -n "$FRONTEND_PID" ]; then
    echo ""
    echo "✨ Both services are ALREADY ACTIVE on localhost!"
    echo "🌐 Frontend Dashboard: http://localhost:5173"
    echo "🔌 Backend API:        http://localhost:8000"
    echo "📖 Swagger API Docs:   http://localhost:8000/docs"
    echo "🩺 Health Check:       http://localhost:8000/health"
    echo ""
    echo "To view or restart them, you can stop the existing processes or run with --restart flag."
    if [ "$1" != "--restart" ]; then
        exit 0
    fi
fi

if [ "$1" = "--restart" ]; then
    if [ -n "$BACKEND_PID" ]; then
        echo "🛑 Stopping existing backend (PID: $BACKEND_PID)..."
        kill -9 $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        echo "🛑 Stopping existing frontend (PID: $FRONTEND_PID)..."
        kill -9 $FRONTEND_PID 2>/dev/null || true
    fi
fi

# 5. Trap cleanup on exit
trap 'echo "🛑 Stopping local servers..."; kill 0 2>/dev/null || true; exit 0' SIGINT SIGTERM EXIT

echo ""
echo "=========================================================="
echo " Starting Localhost Servers in Parallel:"
echo "   - Backend:  http://localhost:8000  (Docs: http://localhost:8000/docs)"
echo "   - Frontend: http://localhost:5173"
echo "=========================================================="
echo "Press Ctrl+C to terminate both servers."
echo ""

# Start FastAPI backend
"$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Start Vite frontend
(cd "$DIR/frontend" && npm run dev -- --host 0.0.0.0) &

wait
