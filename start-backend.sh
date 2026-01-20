#!/bin/bash
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Create data directories if they don't exist
mkdir -p data/audio data/voice_samples

# Start the server
echo ""
echo "Starting Storyteller Backend on http://localhost:8001"
echo "Press Ctrl+C to stop"
echo ""
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
