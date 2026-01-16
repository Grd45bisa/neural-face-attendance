#!/bin/bash

echo "========================================"
echo "  Face Attendance System - Frontend"
echo "========================================"
echo ""

cd frontend

# Check if build exists
if [ ! -d "dist" ]; then
    echo "Build folder not found. Building..."
    npm run build
fi

echo ""
echo "Starting frontend server on http://localhost:3000"
echo "Press Ctrl+C to stop"
echo ""

# Check if serve is installed
if ! command -v serve &> /dev/null; then
    echo "Installing serve..."
    npm install -g serve
fi

# Serve production build
serve -s dist -p 3000
