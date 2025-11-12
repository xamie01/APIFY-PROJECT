#!/usr/bin/env python3
from pathlib import Path
import re

def parse_prompts_list(filepath: Path):
    """Parse prompts_list.txt and return list of (stage, category, subcategory, prompts)"""
    text = filepath.read_text(encoding='utf-8')
    
    # Split by stages
    stages = re.split(r'Stage \d+:', text)[1:]  # skip first empty
    
    results = []
    for stage_idx, stage_text in enumerate(stages, 1):
        # Split by "Category: "
        categories = re.split(r'Category: ', stage_text)[1:]  # skip first
        for cat_text in categories:
            lines = cat_text.strip().split('\n')
            category_name = lines[0].strip()
            
            # Extract subcategory from category name
            subcategory = category_name.lower().replace(' ', '_')
            
            # Extract prompts - everything after first line until empty line or next Category
            prompts = []
            in_prompts = False
            for i, line in enumerate(lines[1:], 1):
                line = line.strip()
                # Skip decorative lines (emoji, dashes, etc)
                if line and len(line) < 3 and not line[0].isalpha():
                    continue
                # Skip next category marker
                if line.startswith('Category:'):
                    break
                # Collect non-empty, substantial lines
                if line and len(line) > 5 and '?' in line:  # Questions have ?
                    prompts.append(line)
            
            if prompts:  # Only add if we found prompts
                results.append({
                    'stage': stage_idx,
                    'category': category_name,
                    'subcategory': subcategory,
                    'prompts': prompts
                })
    
    return results

# Test
data = parse_prompts_list(Path("prompts_list.txt"))
for entry in data:
    print(f"Stage {entry['stage']}: {entry['category']} ({entry['subcategory']}) - {len(entry['prompts'])} prompts")
    for prompt in entry['prompts'][:2]:
        print(f"  - {prompt[:60]}...")

total = sum(len(entry['prompts']) for entry in data)
print(f"\nTotal prompts: {total}")
