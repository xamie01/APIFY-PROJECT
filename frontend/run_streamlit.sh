#!/bin/bash
# Quick start script for O-SATE Streamlit Frontend

echo "🚀 Starting O-SATE Streamlit Frontend..."
echo ""

# Check if we're in the frontend directory
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: streamlit_app.py not found!"
    echo "Please run this script from the frontend directory."
    exit 1
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if parent dependencies are installed
if ! python -c "import src.utils" &> /dev/null; then
    echo "⚠️  O-SATE dependencies not found. Installing..."
    cd .. && pip install -r requirements.txt && cd frontend
fi

echo "✅ All dependencies ready!"
echo ""
echo "🌟 Starting Streamlit app on http://localhost:8501"
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the Streamlit app
streamlit run streamlit_app.py
