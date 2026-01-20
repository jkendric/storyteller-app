#!/bin/bash
SCRIPT_DIR="$(dirname "$0")"

echo "Starting Storyteller Application..."
echo ""

# Start backend in background
"$SCRIPT_DIR/start-backend.sh" &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend in background
"$SCRIPT_DIR/start-frontend.sh" &
FRONTEND_PID=$!

echo ""
echo "Both services are starting..."
echo ""
echo "Backend:  http://localhost:8001"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Wait for both processes
wait
