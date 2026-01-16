#!/bin/bash

echo "========================================"
echo "  Face Attendance System - Backend"
echo "========================================"
echo ""

cd backend

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "WARNING: Virtual environment not found"
    echo "Run: python3 -m venv venv"
    exit 1
fi

# Set environment to production
export FLASK_ENV=production
export FLASK_DEBUG=False

# Create logs folder if not exists
mkdir -p logs

echo ""
echo "Starting backend server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

# Start server with gunicorn (production)
gunicorn -w 4 \
    -b 0.0.0.0:5000 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    app:app

# If gunicorn not installed, install it
if [ $? -ne 0 ]; then
    echo ""
    echo "Gunicorn not found. Installing..."
    pip install gunicorn
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
fi
