#!/bin/bash
# Quick test runner script

source venv/bin/activate
pytest tests/ -v --cov=src --cov-report=html
echo ""
echo "Coverage report generated in htmlcov/index.html"
