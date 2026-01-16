#!/bin/bash
# Quick setup script for Flask backend (Linux/Mac)

echo "========================================"
echo "Flask Backend Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from python.org"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "[4/5] Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created. Please edit it with your settings."
else
    echo ".env file already exists."
fi

echo "[5/5] Creating data directory..."
if [ ! -d ../data ]; then
    mkdir -p ../data
    echo "Data directory created."
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Make sure MongoDB is installed and running"
echo "2. Edit .env file with your configuration"
echo "3. Run: python app.py"
echo ""
echo "For MongoDB installation:"
echo "- Ubuntu: sudo apt-get install mongodb"
echo "- Mac: brew install mongodb-community"
echo "- Start: sudo systemctl start mongod (Linux)"
echo "         brew services start mongodb-community (Mac)"
echo ""
