# O-SATE Streamlit Web Frontend

A beautiful, modern web interface for the O-SATE AI safety testing platform, built with Streamlit for an elegant and interactive user experience.

## 🎨 Design Features

### Modern & Beautiful UI
- **Gradient Backgrounds**: Eye-catching purple gradient backgrounds with modern design
- **Glassmorphism Effects**: Semi-transparent cards with backdrop blur for a modern look
- **Smooth Animations**: Fade-in animations, hover effects, and transitions
- **Custom Styling**: Enhanced CSS with Inter font and professional color schemes
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

### Interactive Components
- **Icon Menu Navigation**: Beautiful sidebar with icons for each section
- **Real-time Metrics**: Live system status with animated metric cards
- **Tabbed Interfaces**: Organized content with stylish tab navigation
- **Expandable Sections**: Collapsible sections for better content organization
- **Progress Indicators**: Visual feedback for long-running operations

## 🚀 Getting Started

### Prerequisites
- Python 3.12 or higher
- All O-SATE core dependencies installed
- Docker (for sandbox features)
- OpenRouter API key (free at openrouter.ai)

### Installation

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Streamlit and dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   - Ensure your main O-SATE `.env` file is configured with API keys
   - The frontend uses the same configuration as the core system

4. **Run the Streamlit app**:
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Access the web interface**:
   - Your browser should automatically open to `http://localhost:8501`
   - If not, navigate to the URL shown in the terminal

## 📱 Features

### 1. Home Dashboard
- **Welcome Section**: Beautiful hero section with branding
- **Feature Cards**: Three prominent cards showcasing main features
- **System Metrics**: Real-time display of active wrappers, sandboxes, and test results
- **Quick Start Guide**: Expandable guide for new users

### 2. AI Model Testing
- **Model Selection**: Choose from 10+ free AI models via OpenRouter
- **Advanced Parameters**: Adjust temperature and max tokens
- **Interactive Query Interface**: Large text area for prompts
- **Real-time Responses**: Immediate display of AI responses
- **Performance Metrics**: Response time, total requests, and averages

### 3. Sandbox Management
- **Create Sandbox**: Easy sandbox creation with custom names
- **Execute Code**: Run commands in isolated Docker containers
- **View Statistics**: Monitor CPU, memory, and container status
- **Tabbed Interface**: Organized workflow for different operations

### 4. Safety Testing Dashboard
- **Predefined Test Types**: 
  - Compliance Testing
  - Dangerous Capabilities
  - Instrumental Convergence
  - Ethical Alignment
  - Bias Detection
- **Custom Prompts**: Edit or add your own test prompts
- **Batch Testing**: Run multiple tests automatically
- **Results History**: View and compare previous test runs
- **Detailed Reports**: Expandable results for each test

## 🎯 Usage Examples

### Running an AI Query
1. Navigate to **AI Testing** page
2. Select a model from the dropdown
3. Optionally adjust temperature and max tokens in Advanced Parameters
4. Enter your prompt in the text area
5. Click **Submit Query**
6. View the response and metrics

### Creating and Using a Sandbox
1. Navigate to **Sandbox** page
2. Go to the **Create Sandbox** tab
3. Enter a unique sandbox name
4. Click **Create Sandbox**
5. Switch to **Execute Code** tab
6. Enter the sandbox name and command
7. Click **Execute** to run the command

### Running Safety Tests
1. Navigate to **Safety Tests** page
2. Select a test type from the dropdown
3. Choose a model to test
4. Review or edit the test prompts
5. Click **Run Safety Tests**
6. Monitor progress and view results
7. Check previous test runs at the bottom

## 🎨 Customization

### Styling
The app uses custom CSS defined in `load_custom_css()` function. You can modify:
- **Colors**: Change gradient colors in the CSS
- **Fonts**: Modify the font-family imports
- **Animations**: Adjust animation timing and effects
- **Layout**: Customize spacing and sizes

### Adding New Pages
1. Create a new render function (e.g., `render_new_page()`)
2. Add the page to the sidebar menu in `option_menu()`
3. Add a condition in the main() function to call your render function

### Theme Customization
Edit `.streamlit/config.toml` to customize:
- Primary colors
- Background colors
- Font settings
- Layout options

## 🔧 Configuration

### Streamlit Config
Create `.streamlit/config.toml` in the frontend directory:

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
address = "0.0.0.0"
headless = true
```

### Environment Variables
The app uses the main O-SATE configuration:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `OPENAI_API_KEY`: Optional, for OpenAI models
- Other provider keys as needed

## 🚀 Deployment

### Local Deployment
```bash
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

### Docker Deployment
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Cloud Deployment
Streamlit apps can be deployed to:
- **Streamlit Cloud**: Free hosting for Streamlit apps
- **Heroku**: With buildpack for Streamlit
- **AWS/GCP/Azure**: Using Docker containers
- **DigitalOcean**: App Platform with Dockerfile

## 🎭 Design Philosophy

### Modern Aesthetics
- Clean, minimalist design
- Generous white space
- Consistent color scheme
- Professional typography

### User Experience
- Intuitive navigation
- Clear visual hierarchy
- Immediate feedback
- Error handling with helpful messages

### Performance
- Lazy loading of components
- Efficient state management
- Caching of expensive operations
- Progress indicators for long tasks

## 🔒 Security

- **No client-side API keys**: All API keys remain server-side
- **Input validation**: All user inputs are validated
- **Sandbox isolation**: Code execution in isolated containers
- **Error handling**: Safe error messages without exposing internals

## 📊 Comparison: Streamlit vs Flask Frontend

### Streamlit Advantages
✅ Modern, beautiful UI out of the box
✅ Built-in responsive design
✅ Interactive components without custom JavaScript
✅ Automatic state management
✅ Faster development time
✅ Better for data apps and dashboards
✅ Native Python all the way

### Flask Advantages
✅ More control over HTML/CSS/JS
✅ RESTful API endpoints
✅ Better for traditional web apps
✅ More flexible routing

## 🐛 Troubleshooting

### Port Already in Use
```bash
streamlit run streamlit_app.py --server.port=8502
```

### Module Import Errors
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure parent directory in path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
```

### Streamlit Not Found
```bash
pip install streamlit==1.29.0
```

### Docker Issues
```bash
# Ensure Docker is running
sudo systemctl start docker

# Check Docker status
docker ps
```

## 🎯 Future Enhancements

- [ ] User authentication and sessions
- [ ] Real-time WebSocket updates
- [ ] Advanced data visualization with Plotly
- [ ] Export test reports to PDF
- [ ] Scheduled test runs
- [ ] Multi-user workspaces
- [ ] Dark mode toggle
- [ ] Model comparison view
- [ ] Historical trends and analytics
- [ ] Custom test suite builder

## 📚 Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Gallery](https://streamlit.io/gallery)
- [O-SATE GitHub](https://github.com/xamie01/O-SATE)
- [OpenRouter API](https://openrouter.ai/docs)

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit a pull request

## 📝 License

This frontend is part of the O-SATE project and uses the same MIT License.

## 💬 Support

For issues or questions:
- Create an issue on [GitHub](https://github.com/xamie01/O-SATE/issues)
- Refer to the main O-SATE documentation
- Check the troubleshooting section above

---

**Built with Streamlit 🎈 and ❤️ for AI Safety Research**
