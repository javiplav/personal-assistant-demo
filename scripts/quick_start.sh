#!/bin/bash

# Quick Start Script for Personal Assistant
# =========================================

echo "🚀 Personal Assistant - Quick Start"
echo "===================================="
echo ""

# Check if setup is complete
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Running setup first..."
    ./setup.sh
    if [ $? -ne 0 ]; then
        echo "❌ Setup failed. Please check the error messages above."
        exit 1
    fi
    echo ""
fi

echo "🌐 Starting Personal Assistant Web Interface..."
echo "💡 The interface will open at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the web interface
source .venv/bin/activate
python scripts/start_web.py
