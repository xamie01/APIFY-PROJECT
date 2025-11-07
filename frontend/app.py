"""
O-SATE Web Frontend
A Flask-based web interface for the O-SATE AI safety testing platform
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import O-SATE modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import json

# Import O-SATE core modules
from src.target_ai_wrapper import TargetAIWrapper
from src.sandbox_manager import SandboxManager
from src.utils import load_config, get_api_key
from src.logger import get_logger

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)  # Enable CORS for API endpoints

# Initialize logger
logger = get_logger(__name__)

# Load O-SATE configuration
# Set working directory to project root for config loading
project_root = Path(__file__).parent.parent
os.chdir(project_root)
config = load_config()

# Store active AI wrappers and sandboxes
ai_wrappers = {}
sandbox_managers = {}


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/ai-testing')
def ai_testing():
    """AI model testing interface"""
    # Get available models from config
    models = config.get('target_ai', {}).get('openrouter_models', [])
    return render_template('ai_testing.html', models=models)


@app.route('/sandbox')
def sandbox():
    """Sandbox management interface"""
    return render_template('sandbox.html')


@app.route('/safety-tests')
def safety_tests():
    """Safety testing dashboard"""
    return render_template('safety_tests.html')


# ============ API Endpoints ============

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available AI models"""
    try:
        models = config.get('target_ai', {}).get('openrouter_models', [])
        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/query', methods=['POST'])
def query_model():
    """Submit a query to an AI model"""
    try:
        data = request.json
        model_name = data.get('model')
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        if not model_name or not prompt:
            return jsonify({
                'success': False,
                'error': 'Model name and prompt are required'
            }), 400
        
        # Create or get AI wrapper for this model
        if model_name not in ai_wrappers:
            ai_wrappers[model_name] = TargetAIWrapper(model_name)
        
        ai = ai_wrappers[model_name]
        
        # Query the model
        start_time = datetime.now()
        response = ai.query(prompt, temperature=temperature, max_tokens=max_tokens)
        end_time = datetime.now()
        
        # Get metrics
        metrics = ai.get_metrics()
        
        return jsonify({
            'success': True,
            'response': response,
            'model': model_name,
            'metrics': {
                'response_time': (end_time - start_time).total_seconds(),
                'total_requests': metrics.get('total_requests', 0),
                'average_response_time': metrics.get('average_response_time', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error querying model: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metrics/<model>', methods=['GET'])
def get_model_metrics(model):
    """Get metrics for a specific model"""
    try:
        if model not in ai_wrappers:
            return jsonify({
                'success': False,
                'error': 'Model not initialized'
            }), 404
        
        ai = ai_wrappers[model]
        metrics = ai.get_metrics()
        
        return jsonify({
            'success': True,
            'model': model,
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sandbox/create', methods=['POST'])
def create_sandbox():
    """Create a new sandbox container"""
    try:
        data = request.json
        name = data.get('name', f'osate-sandbox-{datetime.now().timestamp()}')
        
        # Create sandbox manager if not exists
        if 'default' not in sandbox_managers:
            sandbox_managers['default'] = SandboxManager()
        
        manager = sandbox_managers['default']
        container = manager.create_sandbox(name)
        
        return jsonify({
            'success': True,
            'sandbox_id': container.id,
            'sandbox_name': name
        })
        
    except Exception as e:
        logger.error(f"Error creating sandbox: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sandbox/execute', methods=['POST'])
def execute_in_sandbox():
    """Execute code in a sandbox"""
    try:
        data = request.json
        sandbox_name = data.get('sandbox_name')
        command = data.get('command')
        
        if not sandbox_name or not command:
            return jsonify({
                'success': False,
                'error': 'Sandbox name and command are required'
            }), 400
        
        # Get sandbox manager
        if 'default' not in sandbox_managers:
            return jsonify({
                'success': False,
                'error': 'No sandbox manager initialized'
            }), 400
        
        manager = sandbox_managers['default']
        
        # Execute command
        result = manager.execute_in_sandbox(sandbox_name, command)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error executing in sandbox: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sandbox/stats/<name>', methods=['GET'])
def get_sandbox_stats(name):
    """Get statistics for a sandbox"""
    try:
        if 'default' not in sandbox_managers:
            return jsonify({
                'success': False,
                'error': 'No sandbox manager initialized'
            }), 400
        
        manager = sandbox_managers['default']
        stats = manager.get_container_stats(name)
        
        return jsonify({
            'success': True,
            'sandbox_name': name,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting sandbox stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sandbox/<name>', methods=['DELETE'])
def remove_sandbox(name):
    """Remove a sandbox container"""
    try:
        if 'default' not in sandbox_managers:
            return jsonify({
                'success': False,
                'error': 'No sandbox manager initialized'
            }), 400
        
        manager = sandbox_managers['default']
        manager.remove_sandbox(name)
        
        return jsonify({
            'success': True,
            'message': f'Sandbox {name} removed'
        })
        
    except Exception as e:
        logger.error(f"Error removing sandbox: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test/run', methods=['POST'])
def run_safety_test():
    """Run a safety test suite"""
    try:
        data = request.json
        test_type = data.get('test_type')
        model = data.get('model')
        prompts = data.get('prompts', [])
        
        if not test_type or not model:
            return jsonify({
                'success': False,
                'error': 'Test type and model are required'
            }), 400
        
        # Create AI wrapper
        if model not in ai_wrappers:
            ai_wrappers[model] = TargetAIWrapper(model)
        
        ai = ai_wrappers[model]
        
        # Run tests
        results = []
        for prompt in prompts:
            try:
                response = ai.query(prompt)
                results.append({
                    'prompt': prompt,
                    'response': response,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'prompt': prompt,
                    'error': str(e),
                    'success': False
                })
        
        return jsonify({
            'success': True,
            'test_type': test_type,
            'model': model,
            'results': results,
            'total': len(results),
            'successful': sum(1 for r in results if r['success'])
        })
        
    except Exception as e:
        logger.error(f"Error running safety test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_wrappers': len(ai_wrappers),
        'active_sandboxes': len(sandbox_managers)
    })


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Configuration
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting O-SATE Web Frontend on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    # Run the app
    app.run(host=host, port=port, debug=debug)
