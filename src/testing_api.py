#!/usr/bin/env python3
"""
O-SATE Testing API
Provides REST endpoints for safety test management and execution
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from threading import Thread

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils import load_config
from scripts.run_safety_tests import SafetyTestRunner


class TestingAPI:
    """API handler for safety testing operations"""
    
    def __init__(self):
        self.prompts_dir = ROOT / "prompts"
        self.results_dir = ROOT / "outputs" / "safety_tests"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.current_test = None
        self.test_progress = 0
    
    def get_available_models(self):
        """Get list of available models for testing"""
        try:
            config = load_config()
            models = config.get('target_ai', {}).get('openrouter_models', [])
            return {
                'status': 'success',
                'models': models,
                'count': len(models)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_prompt_categories(self):
        """Get all available prompt categories and subcategories"""
        try:
            categories = {}
            
            for category_dir in self.prompts_dir.iterdir():
                if category_dir.is_dir() and not category_dir.name.startswith('.'):
                    subcategories = {}
                    
                    for subcat_dir in category_dir.iterdir():
                        if subcat_dir.is_dir() and not subcat_dir.name.startswith('.'):
                            json_files = [f for f in subcat_dir.glob('*.json') if f.name != '.gitkeep']
                            subcategories[subcat_dir.name] = {
                                'count': len(json_files),
                                'files': [f.stem for f in json_files]
                            }
                    
                    if subcategories:
                        total = sum(sub['count'] for sub in subcategories.values())
                        categories[category_dir.name] = {
                            'subcategories': subcategories,
                            'total': total
                        }
            
            return {
                'status': 'success',
                'categories': categories,
                'total_prompts': sum(cat['total'] for cat in categories.values())
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def run_safety_test(self, models, category=None, subcategory=None, limit=None):
        """Run safety tests and return results"""
        try:
            runner = SafetyTestRunner()
            runner.run(
                models=models,
                category=category,
                subcategory=subcategory,
                limit=limit
            )
            
            # Get summary
            summary = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'models': models,
                'category': category,
                'subcategory': subcategory,
                'tests_run': len(runner.test_log),
                'results_by_category': dict(runner.results)
            }
            
            return {
                'status': 'success',
                'summary': summary,
                'test_log': runner.test_log,
                'results': dict(runner.results)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_test_results(self, limit=10):
        """Get recent test results"""
        try:
            results = []
            result_files = sorted(
                self.results_dir.glob('test_results_*.json'),
                reverse=True
            )[:limit]
            
            for result_file in result_files:
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        results.append({
                            'filename': result_file.name,
                            'timestamp': data.get('timestamp'),
                            'test_count': data.get('test_count'),
                            'summary': data.get('summary'),
                            'date': result_file.stat().st_mtime
                        })
                except json.JSONDecodeError:
                    pass
            
            return {
                'status': 'success',
                'results': results,
                'count': len(results)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_test_statistics(self):
        """Get aggregated statistics from all tests"""
        try:
            stats = {
                'total_tests_run': 0,
                'total_prompts_tested': 0,
                'overall_refusal_rate': 0.0,
                'by_category': {},
                'by_model': {},
                'latest_test': None
            }
            
            passed_count = 0
            total_count = 0
            result_files = list(self.results_dir.glob('test_results_*.json'))
            
            if not result_files:
                return {
                    'status': 'success',
                    'statistics': stats,
                    'message': 'No tests run yet'
                }
            
            for result_file in result_files:
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        stats['total_tests_run'] += 1
                        
                        # Get latest
                        if not stats['latest_test'] or data['timestamp'] > stats['latest_test']['timestamp']:
                            stats['latest_test'] = {
                                'timestamp': data['timestamp'],
                                'test_count': data.get('test_count')
                            }
                        
                        # Aggregate results
                        for test in data.get('tests', []):
                            total_count += 1
                            if test.get('passed'):
                                passed_count += 1
                            
                            # By model
                            model = test.get('model', 'unknown')
                            if model not in stats['by_model']:
                                stats['by_model'][model] = {'passed': 0, 'failed': 0}
                            if test.get('passed'):
                                stats['by_model'][model]['passed'] += 1
                            else:
                                stats['by_model'][model]['failed'] += 1
                        
                        # By category
                        for cat, res in data.get('summary', {}).items():
                            if cat not in stats['by_category']:
                                stats['by_category'][cat] = res
                except (json.JSONDecodeError, KeyError):
                    pass
            
            stats['total_prompts_tested'] = total_count
            if total_count > 0:
                stats['overall_refusal_rate'] = (passed_count / total_count)
            
            return {
                'status': 'success',
                'statistics': stats
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_prompt_details(self, category, subcategory, prompt_id):
        """Get details of a specific prompt"""
        try:
            prompt_file = self.prompts_dir / category / subcategory / f"{prompt_id}.json"
            
            if not prompt_file.exists():
                return {'status': 'error', 'message': 'Prompt not found'}
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
            
            return {
                'status': 'success',
                'prompt': prompt_data
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


# Create API instance
api = TestingAPI()


def setup_flask_routes(app):
    """Set up Flask routes for testing API"""
    from flask import jsonify, request
    
    @app.route('/api/tests/models', methods=['GET'])
    def test_get_models():
        return jsonify(api.get_available_models())
    
    @app.route('/api/tests/categories', methods=['GET'])
    def test_get_categories():
        return jsonify(api.get_prompt_categories())
    
    @app.route('/api/tests/run', methods=['POST'])
    def test_run():
        try:
            data = request.get_json()
            models = data.get('models', ['openrouter-mistral-7b'])
            category = data.get('category')
            subcategory = data.get('subcategory')
            limit = data.get('limit')
            
            result = api.run_safety_test(
                models=models,
                category=category,
                subcategory=subcategory,
                limit=limit
            )
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
    
    @app.route('/api/tests/results', methods=['GET'])
    def test_get_results():
        limit = request.args.get('limit', 10, type=int)
        return jsonify(api.get_test_results(limit=limit))
    
    @app.route('/api/tests/statistics', methods=['GET'])
    def test_get_statistics():
        return jsonify(api.get_test_statistics())
    
    @app.route('/api/tests/prompt/<category>/<subcategory>/<prompt_id>', methods=['GET'])
    def test_get_prompt(category, subcategory, prompt_id):
        return jsonify(api.get_prompt_details(category, subcategory, prompt_id))
