# O-SATE Web Frontend

A web-based interface for the O-SATE (Open-Source Safety Assessment and Testing Environment) platform.

## 🎨 **NEW: Modern Streamlit UI Available!**

We now offer a beautiful, modern Streamlit-based frontend with enhanced UI/UX! See [STREAMLIT_README.md](STREAMLIT_README.md) for details.

**Quick Start with Streamlit:**
```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Overview

This directory contains **two frontend options**:

1. **Streamlit Frontend** (⭐ Recommended) - Modern, beautiful UI built with Streamlit
   - File: `streamlit_app.py` or `streamlit_demo.py` (demo version)
   - Gradient backgrounds, glassmorphism effects, smooth animations
   - Interactive components with icon navigation
   - Built-in responsive design

2. **Flask Frontend** (Legacy) - Traditional web application
   - File: `app.py`
   - RESTful API endpoints
   - Custom HTML/CSS/JS templates

Both frontends provide:

- Test AI models from multiple providers (OpenRouter, OpenAI, Google, Anthropic, etc.)
- Execute code safely in isolated Docker sandbox environments
- Monitor AI model metrics and performance
- Run safety assessment tests
- View and analyze results in real-time

## Architecture

### Streamlit Frontend (NEW)
- **Framework**: Streamlit (modern Python web framework)
- **UI**: Custom CSS with gradient backgrounds and animations
- **Components**: streamlit-option-menu for navigation
- **State Management**: Built-in Streamlit session state

### Flask Frontend (Legacy)
- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Bootstrap 5 for responsive design
- **API Integration**: Direct integration with O-SATE core modules

## Features

### 1. AI Model Testing Interface
- Select from 10+ free AI models via OpenRouter
- Interactive query interface
- Real-time response display
- Model metrics and statistics

### 2. Sandbox Management
- Create and manage Docker sandbox containers
- Execute code in isolated environments
- Monitor resource usage (CPU, memory)
- View execution logs and results

### 3. Safety Testing Dashboard
- Run predefined safety test suites
- Test for dangerous capabilities
- Compliance testing
- Instrumental convergence detection

### 4. Results Visualization
- View test results and metrics
- Export results to JSON/CSV
- Historical test tracking

## Installation

### Prerequisites

- Python 3.12+
- All O-SATE core dependencies installed
- Docker (for sandbox features)

### Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install frontend-specific dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   - Ensure your main O-SATE `.env` file is configured with API keys
   - The frontend uses the same configuration as the core system

## Running the Frontend

### Option 1: Streamlit Frontend (Recommended)

**Using the demo version (no dependencies required):**
```bash
streamlit run streamlit_demo.py
```

**Using the full version (requires O-SATE dependencies):**
```bash
streamlit run streamlit_app.py
```

**Or use the quick start script:**
```bash
./run_streamlit.sh
```

Access at: `http://localhost:8501`

### Option 2: Flask Frontend (Legacy)

**Run the Flask server:**
```bash
python app.py
   ```

3. **Configure environment variables**:
   - Ensure your main O-SATE `.env` file is configured with API keys
   - The frontend uses the same configuration as the core system

4. **Run the web server**:
   ```bash
   python app.py
   ```
   
   Or use Flask's development server:
   ```bash
   flask run --host=0.0.0.0 --port=5000
   ```

5. **Access the web interface**:
   - Open your browser and navigate to: `http://localhost:5000`

## Usage

### Starting the Server

```bash
# From the frontend directory
python app.py
```

The server will start on `http://localhost:5000` by default.

### Testing AI Models

1. Navigate to the **AI Testing** page
2. Select a model from the dropdown
3. Enter your prompt in the text area
4. Click "Submit Query"
5. View the AI response and metrics

### Using the Sandbox

1. Navigate to the **Sandbox** page
2. Create a new sandbox container
3. Enter code to execute
4. Click "Execute"
5. View the output and execution statistics

### Running Safety Tests

1. Navigate to the **Safety Tests** page
2. Select a test suite (compliance, dangerous capabilities, etc.)
3. Choose models to test
4. Click "Run Tests"
5. View results and analysis

## API Endpoints

The frontend provides a RESTful API:

### AI Testing
- `POST /api/query` - Submit a query to an AI model
- `GET /api/models` - Get list of available models
- `GET /api/metrics/<model>` - Get metrics for a specific model

### Sandbox Management
- `POST /api/sandbox/create` - Create a new sandbox
- `POST /api/sandbox/execute` - Execute code in sandbox
- `GET /api/sandbox/stats/<name>` - Get sandbox statistics
- `DELETE /api/sandbox/<name>` - Remove a sandbox

### Safety Testing
- `POST /api/test/run` - Run a safety test suite
- `GET /api/test/results/<id>` - Get test results
- `GET /api/test/history` - Get test history

## File Structure

```
frontend/
├── app.py                 # Main Flask application
├── requirements.txt       # Frontend dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Home page
│   ├── ai_testing.html   # AI model testing interface
│   ├── sandbox.html      # Sandbox management
│   └── safety_tests.html # Safety testing dashboard
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # Frontend JavaScript
└── config.py             # Flask configuration
```

## Configuration

### Flask Settings

Edit `config.py` to customize:

```python
DEBUG = True  # Set to False in production
HOST = '0.0.0.0'  # Allow external connections
PORT = 5000  # Web server port
SECRET_KEY = 'your-secret-key'  # For session management
```

### O-SATE Integration

The frontend automatically uses the O-SATE configuration from:
- `../config/default_config.yaml`
- `../.env` (for API keys)

## Development

### Adding New Features

1. **New Route**: Add to `app.py`
2. **New Template**: Create in `templates/`
3. **New Styles**: Add to `static/css/style.css`
4. **New JavaScript**: Add to `static/js/main.js`

### Testing

```bash
# Run Flask in debug mode
export FLASK_ENV=development
python app.py
```

### Code Style

Follow PEP 8 guidelines for Python code:
```bash
black app.py
flake8 app.py
```

## Footer & Contact Configuration

The homepage footer includes:
- **About Us**: Information about O-SATE
- **FAQs**: Common questions and answers
- **Contact Us**: A contact form for user inquiries
- **Privacy Policy**: Data privacy and security information
- **Copyright & Disclaimer**: Legal information and usage restrictions

### Setting Up Contact Email

To receive contact form submissions, configure your email address:

**Option 1: Via Configuration File**
Edit `../config/default_config.yaml`:
```yaml
contact:
  email: "your-email@example.com"
```

**Option 2: Via Environment Variable**
```bash
export CONTACT_EMAIL="your-email@example.com"
```

**Option 3: Using .env File**
Create or edit `../.env`:
```
CONTACT_EMAIL=your-email@example.com
```

Messages will be logged to the backend console and can be integrated with an email service like SendGrid, Mailgun, or AWS SES for production use.

## Security Considerations

- **API Keys**: Never expose API keys in the frontend
- **Input Validation**: All user inputs are validated server-side
- **Sandbox Isolation**: Code execution is isolated in Docker containers
- **Rate Limiting**: Implement rate limiting for API endpoints
- **HTTPS**: Use HTTPS in production environments

## Troubleshooting

### Port Already in Use
```bash
# Change the port in app.py or use:
python app.py --port 5001
```

### Cannot Connect to Docker
```bash
# Ensure Docker daemon is running
sudo systemctl start docker
```

### Module Import Errors
```bash
# Install dependencies
pip install -r requirements.txt

# Add parent directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
```

## Future Enhancements

- [ ] User authentication and sessions
- [ ] Multi-user support with separate workspaces
- [ ] WebSocket support for real-time updates
- [ ] Advanced data visualization with Chart.js
- [ ] Export test reports to PDF
- [ ] Scheduled test runs
- [ ] REST API documentation with Swagger
- [ ] Docker Compose setup for easy deployment

## Contributing

Contributions are welcome! Please:

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit a pull request

## License

This frontend is part of the O-SATE project and uses the same MIT License.

## Support

For issues or questions:
- Create an issue on GitHub
- Refer to the main O-SATE documentation
- Check the troubleshooting section above

---

**Built with Flask and ❤️ for AI Safety Research**
