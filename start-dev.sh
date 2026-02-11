#!/bin/bash

# Alpaca Development Environment Startup Script
# This script helps you start both frontend and backend servers

echo "🦙 Starting Alpaca Development Environment..."
echo ""

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env file not found!"
    echo "Please copy backend/.env.example to backend/.env and configure it."
    exit 1
fi

if [ ! -f ".env.local" ]; then
    echo "❌ Error: .env.local file not found!"
    echo "Please create .env.local with VITE_API_BASE_URL=http://localhost:8000"
    exit 1
fi

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ] && [ ! -f "backend/.venv" ]; then
    echo "⚠️  Warning: Python virtual environment not found."
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Check if frontend dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo ""
echo "✅ Environment checks complete!"
echo ""
echo "Starting servers..."
echo "- Backend will run on: http://localhost:8000"
echo "- Frontend will run on: http://localhost:8081"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "🚀 Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "🚀 Starting frontend server..."
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait