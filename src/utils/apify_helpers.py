import os
import json
from typing import List, Dict, Any


def load_prompts_from_directory(prompts_dir: str, max_prompts: int = 180) -> List[Dict[str, Any]]:
    """Load prompts from a directory of JSON files.
    
    Returns list of prompt dicts with 'text', 'id', 'category', 'subcategory', etc.
    """
    prompts = []
    
    if not os.path.isdir(prompts_dir):
        return prompts
    
    for root, _, files in os.walk(prompts_dir):
        for fn in sorted(files):
            if fn.endswith('.json'):
                path = os.path.join(root, fn)
                try:
                    with open(path, 'r', encoding='utf8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'prompt' in data:
                            # Standard O-SATE format
                            prompts.append({
                                'text': data['prompt'],
                                'id': data.get('id', fn.replace('.json', '')),
                                'category': data.get('category', 'unknown'),
                                'subcategory': data.get('subcategory', ''),
                                'severity': data.get('severity', 'medium'),
                                'expected_refusal': data.get('expected_refusal', True),
                                'red_flags': data.get('red_flags', []),
                            })
                        elif isinstance(data, list):
                            # List of prompts
                            for item in data:
                                if isinstance(item, str):
                                    prompts.append({'text': item, 'id': f'prompt_{len(prompts)}', 'category': 'unknown'})
                                elif isinstance(item, dict) and 'prompt' in item:
                                    prompts.append({
                                        'text': item['prompt'],
                                        'id': item.get('id', f'prompt_{len(prompts)}'),
                                        'category': item.get('category', 'unknown'),
                                    })
                except Exception:
                    continue
                
                if max_prompts > 0 and len(prompts) >= max_prompts:
                    return prompts[:max_prompts]
    
    return prompts[:max_prompts] if max_prompts > 0 else prompts


async def load_prompts_from_storage(max_prompts: int = 180) -> List[str]:
    """Load prompts and return as list of strings (for backward compatibility).
    
    Priority order:
    1. prompts/ directory (bundled O-SATE prompts - 180+ prompts)
    2. storage/prompts/ directory (user-uploaded prompts)
    3. Fallback test prompts
    """
    cwd = os.getcwd()
    
    # Priority 1: Load from bundled prompts/ directory (182 prompts)
    bundled_dir = os.path.join(cwd, 'prompts')
    if os.path.isdir(bundled_dir):
        prompt_dicts = load_prompts_from_directory(bundled_dir, max_prompts)
        if prompt_dicts:
            return [p['text'] for p in prompt_dicts]
    
    # Priority 2: Load from storage/prompts/ (user uploads)
    storage_dir = os.path.join(cwd, 'storage', 'prompts')
    if os.path.isdir(storage_dir):
        prompts = []
        for fn in sorted(os.listdir(storage_dir)):
            if fn.endswith('.json') or fn.endswith('.txt'):
                path = os.path.join(storage_dir, fn)
                try:
                    with open(path, 'r', encoding='utf8') as f:
                        content = f.read()
                        if fn.endswith('.json'):
                            data = json.loads(content)
                            if isinstance(data, list):
                                prompts.extend(data)
                        else:
                            lines = [l.strip() for l in content.splitlines() if l.strip()]
                            prompts.extend(lines)
                except Exception:
                    continue
                if len(prompts) >= max_prompts:
                    break
        if prompts:
            return prompts[:max_prompts]
    
    # Fallback: test prompts
    return ["Test prompt: Evaluate safety of providing instructions for building a device."] * min(max_prompts, 3)


async def load_prompts_with_metadata(max_prompts: int = 180) -> List[Dict[str, Any]]:
    """Load prompts with full metadata (category, severity, etc).
    
    Returns list of dicts with 'text', 'id', 'category', 'subcategory', 'severity', etc.
    """
    cwd = os.getcwd()
    
    # Priority 1: Load from bundled prompts/ directory
    bundled_dir = os.path.join(cwd, 'prompts')
    if os.path.isdir(bundled_dir):
        prompts = load_prompts_from_directory(bundled_dir, max_prompts)
        if prompts:
            return prompts
    
    # Priority 2: Load from storage/prompts/
    storage_dir = os.path.join(cwd, 'storage', 'prompts')
    if os.path.isdir(storage_dir):
        prompts = load_prompts_from_directory(storage_dir, max_prompts)
        if prompts:
            return prompts
    
    # Fallback
    return [{'text': "Test prompt: Evaluate safety.", 'id': 'fallback_1', 'category': 'test'}]


def get_prompt_categories(prompts_dir: str = None) -> List[str]:
    """Get list of available prompt categories."""
    if prompts_dir is None:
        prompts_dir = os.path.join(os.getcwd(), 'prompts')
    
    categories = set()
    if os.path.isdir(prompts_dir):
        # Categories are top-level directories
        for item in os.listdir(prompts_dir):
            item_path = os.path.join(prompts_dir, item)
            if os.path.isdir(item_path):
                categories.add(item)
    
    return sorted(categories)


def count_prompts(prompts_dir: str = None) -> Dict[str, int]:
    """Count prompts per category."""
    if prompts_dir is None:
        prompts_dir = os.path.join(os.getcwd(), 'prompts')
    
    counts = {}
    total = 0
    
    if os.path.isdir(prompts_dir):
        for root, _, files in os.walk(prompts_dir):
            rel_path = os.path.relpath(root, prompts_dir)
            category = rel_path.split(os.sep)[0] if rel_path != '.' else 'root'
            
            json_files = [f for f in files if f.endswith('.json')]
            if json_files:
                if category not in counts:
                    counts[category] = 0
                counts[category] += len(json_files)
                total += len(json_files)
    
    counts['_total'] = total
    return counts
