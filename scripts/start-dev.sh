#!/bin/bash

echo "Starting Poromet Development Environment"
echo "========================================"

# Check if Python dependencies are installed
echo "Checking Python dependencies..."
python -c "import porespy, fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start FastAPI backend in background
echo "Starting FastAPI backend..."
cd api
python analyze.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
curl -s http://127.0.0.1:5328/api/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backend started successfully at http://127.0.0.1:5328"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start Next.js frontend
echo "Starting Next.js frontend..."
echo "Frontend will be available at http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT

# Start frontend (this will block)
npm run dev

# Cleanup if npm run dev exits
cleanup
