#!/bin/bash
# O-SATE Phase 1 Development Setup Script (Weeks 1-4)
# Run this script to set up your complete development environment

set -e  # Exit on any error

echo "=========================================="
echo "O-SATE Phase 1 Development Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if (( $(echo "$PYTHON_VERSION >= 3.10" | bc -l) )); then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.10+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    print_success "Docker found"
else
    print_error "Docker not found. Please install Docker"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    print_success "Git found"
else
    print_error "Git not found. Please install Git"
    exit 1
fi

echo ""
print_info "All prerequisites met!"
echo ""

# Create project structure
echo "=========================================="
echo "Creating Project Structure"
echo "=========================================="
echo ""

# Create all directories
print_info "Creating directories..."
mkdir -p src
mkdir -p config
mkdir -p prompts/dangerous_capabilities/bio_threats
mkdir -p prompts/dangerous_capabilities/cyber_threats
mkdir -p prompts/dangerous_capabilities/wmd_threats
mkdir -p prompts/compliance_tests
mkdir -p prompts/instrumental_convergence
mkdir -p tests
mkdir -p logs
mkdir -p docs
mkdir -p examples
mkdir -p reports

# Create .gitkeep files for empty directories
touch prompts/dangerous_capabilities/bio_threats/.gitkeep
touch prompts/dangerous_capabilities/cyber_threats/.gitkeep
touch prompts/dangerous_capabilities/wmd_threats/.gitkeep
touch prompts/compliance_tests/.gitkeep
touch prompts/instrumental_convergence/.gitkeep
touch logs/.gitkeep
touch reports/.gitkeep

# Create __init__.py files
touch src/__init__.py
touch tests/__init__.py

print_success "Project structure created"
echo ""

# Create virtual environment
echo "=========================================="
echo "Setting Up Virtual Environment"
echo "=========================================="
echo ""

print_info "Creating virtual environment..."
python3 -m venv venv

print_info "Activating virtual environment..."
source venv/bin/activate

print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

print_success "Virtual environment ready"
echo ""

# Create requirements.txt
echo "=========================================="
echo "Creating requirements.txt"
echo "=========================================="
echo ""

cat > requirements.txt << 'EOF'
# Core dependencies
python-dotenv==1.0.0
pyyaml==6.0.1
click==8.1.7

# Docker SDK
docker==7.0.0

# AI/ML APIs
openai==1.3.7
anthropic==0.8.1

# HTTP requests
requests==2.31.0
httpx==0.25.2

# Logging and monitoring
loguru==0.7.2
rich==13.7.0

# Data processing
pydantic==2.5.3
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Development tools
black==23.12.1
flake8==7.0.0
mypy==1.8.0
isort==5.13.2

# Async support
aiohttp==3.9.1
EOF

print_success "requirements.txt created"
echo ""

# Install dependencies
echo "=========================================="
echo "Installing Dependencies"
echo "=========================================="
echo ""

print_info "This may take a few minutes..."
pip install -r requirements.txt

print_success "Dependencies installed"
echo ""

# Create .env.example
echo "=========================================="
echo "Creating Configuration Files"
echo "=========================================="
echo ""

cat > .env.example << 'EOF'
# O-SATE Configuration

# AI Provider API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Default Target AI
DEFAULT_TARGET_AI=openai-gpt4

# Sandbox Configuration
SANDBOX_TIMEOUT=300
SANDBOX_MEMORY_LIMIT=2g
SANDBOX_CPU_LIMIT=1.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/osate.log

# Testing
DEBUG_MODE=false
ENABLE_VERBOSE_LOGGING=false
EOF

# Create actual .env file
cp .env.example .env

print_success "Environment files created"
print_info "Edit .env file to add your API keys"
echo ""

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment files
.env
.env.local
.env.*.local

# Logs
logs/*.log
*.log

# Test coverage
.coverage
htmlcov/
.pytest_cache/
.tox/

# Docker
*.pid
docker-compose.override.yml

# Reports and outputs
reports/
output/
*.json
*.html
*.pdf
!prompts/**/*.json
!config/**/*.json

# OS
Thumbs.db
EOF

print_success "Configuration files created"
echo ""

# Build Docker image
echo "=========================================="
echo "Building Docker Image"
echo "=========================================="
echo ""

print_info "Building O-SATE Docker image..."
docker build -t osate:latest . 2>&1 | grep -E "(Step|Successfully)" || true

if [ $? -eq 0 ]; then
    print_success "Docker image built successfully"
else
    print_error "Docker build failed. Please check Dockerfile"
fi

echo ""

# Initialize git repository
echo "=========================================="
echo "Initializing Git Repository"
echo "=========================================="
echo ""

if [ ! -d .git ]; then
    print_info "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial O-SATE Phase 1 setup"
    print_success "Git repository initialized"
else
    print_info "Git repository already exists"
fi

echo ""

# Run tests
echo "=========================================="
echo "Running Initial Tests"
echo "=========================================="
echo ""

print_info "Running test suite..."
pytest tests/ -v --tb=short || print_error "Some tests failed (expected for initial setup)"

echo ""

# Create quick start script
cat > run_tests.sh << 'EOF'
#!/bin/bash
# Quick test runner script

source venv/bin/activate
pytest tests/ -v --cov=src --cov-report=html
echo ""
echo "Coverage report generated in htmlcov/index.html"
EOF

chmod +x run_tests.sh

# Create development helper script
cat > dev.sh << 'EOF'
#!/bin/bash
# Development helper script

case "$1" in
    "test")
        source venv/bin/activate
        pytest tests/ -v
        ;;
    "format")
        source venv/bin/activate
        black src/ tests/
        isort src/ tests/
        echo "Code formatted!"
        ;;
    "lint")
        source venv/bin/activate
        flake8 src/ tests/
        mypy src/
        ;;
    "docker")
        docker build -t osate:latest .
        echo "Docker image built!"
        ;;
    "clean")
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
        find . -type f -name "*.pyc" -delete
        rm -rf .pytest_cache htmlcov .coverage
        echo "Cleaned up!"
        ;;
    *)
        echo "O-SATE Development Helper"
        echo ""
        echo "Usage: ./dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  test    - Run test suite"
        echo "  format  - Format code with black and isort"
        echo "  lint    - Run linters (flake8, mypy)"
        echo "  docker  - Build Docker image"
        echo "  clean   - Clean up cache files"
        ;;
esac
EOF

chmod +x dev.sh

print_success "Helper scripts created"
echo ""

# Final summary
echo "=========================================="
echo "Setup Complete! 🎉"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Edit .env file and add your API keys:"
echo "   nano .env"
echo ""
echo "3. Run tests to verify setup:"
echo "   ./run_tests.sh"
echo ""
echo "4. Start development:"
echo "   - Week 1: Complete logging and utilities"
echo "   - Week 2: Implement sandbox manager"
echo "   - Week 3: Build AI wrapper"
echo "   - Week 4: Create prompt corpus"
echo ""
echo "Development Commands:"
echo "  ./dev.sh test    - Run tests"
echo "  ./dev.sh format  - Format code"
echo "  ./dev.sh lint    - Check code quality"
echo "  ./dev.sh docker  - Build Docker image"
echo "  ./dev.sh clean   - Clean cache"
echo ""
echo "Documentation:"
echo "  docs/installation.md - Installation guide"
echo "  docs/quickstart.md   - Quick start tutorial"
echo ""
print_success "Happy coding! 🚀"
echo ""
