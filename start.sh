#!/bin/bash

# Drone Swarm Security System — Quick Start Script

set -e

echo "🚁 Drone Swarm Security System — Startup"
echo "========================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 required but not installed"
    exit 1
fi

echo "✓ Python $(python3 --version)"

# Install backend dependencies
if [ ! -d "backend_venv" ]; then
    echo "📦 Creating backend virtual environment..."
    python3 -m venv backend_venv
fi

echo "📦 Installing backend dependencies..."
source backend_venv/bin/activate
pip install -q -r requirements.txt
pip install -q -r backend/requirements.txt

# Start backend
echo "🚀 Starting Flask backend on http://localhost:5000"
python backend/app.py &
BACKEND_PID=$!

# Start frontend server
echo "🌐 Starting frontend server on http://localhost:3000"
if command -v python3 &> /dev/null; then
    cd frontend
    python3 -m http.server 3000 > /dev/null 2>&1 &
    FRONTEND_PID=$!
    cd ..
else
    echo "⚠️  Python HTTP server not available, open frontend/index.html directly"
fi

echo ""
echo "✨ System started!"
echo ""
echo "🎬 Open your browser:"
echo "   http://localhost:3000  (Frontend)"
echo "   http://localhost:5000  (API)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for both processes
wait $BACKEND_PID
