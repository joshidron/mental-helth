@echo off
REM ============================================
REM Prajna Path - Mental Health Web Application
REM Deployment Script for Windows
REM ============================================

echo ==========================================
echo   Prajna Path Deployment Script
echo ==========================================
echo.

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.7 or higher.
    pause
    exit /b 1
)
echo [SUCCESS] Python found
echo.

REM Check if pip is installed
echo [INFO] Checking pip installation...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed. Please install pip.
    pause
    exit /b 1
)
echo [SUCCESS] pip found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    if not exist ".venv" (
        echo [INFO] Creating virtual environment...
        python -m venv venv
        echo [SUCCESS] Virtual environment created
    ) else (
        echo [SUCCESS] Virtual environment already exists
    )
) else (
    echo [SUCCESS] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [INFO] Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Could not find virtual environment activation script
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated
echo.

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [SUCCESS] pip upgraded
echo.

REM Install dependencies
echo [INFO] Installing dependencies from requirements.txt...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed successfully
) else (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)
echo.

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "uploads" mkdir uploads
if not exist "instance" mkdir instance
if not exist "static" mkdir static
echo [SUCCESS] Directories created
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [INFO] Creating .env file...
    (
        echo FLASK_APP=app.py
        echo FLASK_ENV=development
        echo SECRET_KEY=your_secret_key_change_in_production
        echo DATABASE_URI=sqlite:///mental_health.db
    ) > .env
    echo [SUCCESS] .env file created
) else (
    echo [SUCCESS] .env file already exists
)
echo.

REM Initialize database
echo [INFO] Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all()"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to initialize database
    pause
    exit /b 1
)
echo [SUCCESS] Database initialized
echo.

REM Check if AI model exists
if not exist "local_model.pkl" (
    echo [INFO] AI model not found. You may need to train the model from admin panel.
) else (
    echo [SUCCESS] AI model found
)
echo.

echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo [SUCCESS] Application is ready to start
echo.
echo [INFO] Starting Flask application...
echo.
echo Access the application at: http://localhost:5001
echo Admin panel at: http://localhost:5001/admin
echo Default admin credentials: admin / admin123
echo.
echo Press Ctrl+C to stop the server
echo.
echo ==========================================
echo.

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development

REM Start the Flask application
python app.py
