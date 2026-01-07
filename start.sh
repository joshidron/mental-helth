#!/bin/bash

# ============================================
# Prajna Path - Mental Health Web Application
# Deployment Script
# ============================================

echo "=========================================="
echo "  Prajna Path Deployment Script"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if Python is installed
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python 3.7 or higher."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Check if pip is installed
print_info "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    if ! command -v pip &> /dev/null; then
        print_error "pip is not installed. Please install pip."
        exit 1
    else
        PIP_CMD="pip"
    fi
else
    PIP_CMD="pip3"
fi
print_success "pip found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
$PIP_CMD install --upgrade pip --quiet
print_success "pip upgraded"

# Install dependencies
print_info "Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
else
    print_error "requirements.txt not found"
    exit 1
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p uploads
mkdir -p instance
mkdir -p static
print_success "Directories created"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    cat > .env << EOF
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_change_in_production
DATABASE_URI=sqlite:///mental_health.db
EOF
    print_success ".env file created"
else
    print_success ".env file already exists"
fi

# Initialize database
print_info "Initializing database..."
$PYTHON_CMD -c "from app import app, db; app.app_context().push(); db.create_all()"
if [ $? -eq 0 ]; then
    print_success "Database initialized"
else
    print_error "Failed to initialize database"
    exit 1
fi

# Check if AI model exists
if [ ! -f "local_model.pkl" ]; then
    print_info "AI model not found. You may need to train the model from admin panel."
else
    print_success "AI model found"
fi

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
print_success "Application is ready to start"
echo ""
print_info "Starting Flask application..."
echo ""
echo "Access the application at: http://localhost:5001"
echo "Admin panel at: http://localhost:5001/admin"
echo "Default admin credentials: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "=========================================="
echo ""

# Start the Flask application
export FLASK_APP=app.py
export FLASK_ENV=development
$PYTHON_CMD app.py
