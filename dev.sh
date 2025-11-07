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
