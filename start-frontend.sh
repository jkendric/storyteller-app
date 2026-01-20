#!/bin/bash
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the dev server
echo ""
echo "Starting Storyteller Frontend on http://localhost:5173"
echo "Press Ctrl+C to stop"
echo ""
npm run dev
