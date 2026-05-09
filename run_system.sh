#!/bin/bash

echo "========================================"
echo "  AI ATTENDANCE SYSTEM - LAUNCHER"
echo "========================================"
echo

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project directory."
    exit 1
fi

echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python3 found"

echo
echo "[2/4] Installing/Updating dependencies..."
pip3 install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"

echo
echo "[3/4] Setting up database..."
python3 setup_db.py
if [ $? -ne 0 ]; then
    echo "❌ Database setup failed"
    exit 1
fi
echo "✅ Database ready"

echo
echo "[4/4] Starting AI Attendance System..."
echo
echo "🌐 Web Interface: http://localhost:5000"
echo "📱 Mobile Access: http://[YOUR_IP]:5000"
echo
echo "📋 Instructions:"
echo "   1. Open browser and go to http://localhost:5000"
echo "   2. Register your company (first time only)"
echo "   3. Login with admin credentials"
echo "   4. Add employees with photos"
echo "   5. Start camera recognition"
echo
echo "🎯 Press Ctrl+C to stop the system"
echo

python3 app.py