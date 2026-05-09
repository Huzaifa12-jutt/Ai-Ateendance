@echo off
echo ========================================
echo   AI ATTENDANCE SYSTEM - LAUNCHER
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python found

echo.
echo [2/4] Installing/Updating dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo ✅ Dependencies installed

echo.
echo [3/4] Setting up database...
python setup_db.py
if errorlevel 1 (
    echo ❌ Database setup failed
    echo Please check your internet connection for MongoDB Atlas
    pause
    exit /b 1
)
echo ✅ Database ready

echo.
echo [4/4] Starting AI Attendance System...
echo.
echo 🌐 Web Interface: http://localhost:5000
echo 📱 Mobile Access: http://localhost:5000
echo.
echo 📋 Quick Start Guide:
echo    1. Open browser and go to http://localhost:5000
echo    2. Register your company (first time only)
echo    3. Login with admin credentials
echo    4. Add employees with clear photos
echo    5. Click "Test Camera" to verify camera works
echo    6. Click "Start Recognition" to begin attendance monitoring
echo.
echo 🎯 Camera Testing Tips:
echo    - Ensure good lighting
echo    - Face camera directly
echo    - Keep 2-3 feet distance
echo    - Test with "Test Camera" button first
echo.
echo 🛑 To stop: Close this window or press Ctrl+C
echo.

python app.py