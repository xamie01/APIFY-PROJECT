#!/usr/bin/env python3
"""
Generate prompt JSON files from structured templates located in templates/prompts_templates.json
Writes files into prompts/<category>/<subcategory>/<ID>.json
"""
import json
from pathlib import Path
from datetime import datetime
import argparse
import uuid


def load_templates(path: Path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def generate_from_templates(templates, output_dir: Path, count=50, groups=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    groups = groups or ["general"]

    idx = 1
    created = 0
    for category, subs in templates.items():
        for subcategory, entries in subs.items():
            for entry in entries:
                variations = entry.get('variations', {})
                # Create simple combinations by cycling variation values
                # If no variations, create single prompt
                if not variations:
                    for group in groups:
                        if created >= count:
                            return created
                        prompt_text = entry['template'].replace('{group}', group)
                        prompt = build_prompt(category, subcategory, entry, prompt_text, idx, group)
                        write_prompt(output_dir, category, subcategory, prompt)
                        idx += 1
                        created += 1
                else:
                    # prepare cartesian product of variation lists
                    keys = list(variations.keys())
                    lists = [variations[k] for k in keys]
                    import itertools
                    for combo in itertools.product(*lists):
                        if created >= count:
                            return created
                        subs_map = {k: v for k, v in zip(keys, combo)}
                        for group in groups:
                            prompt_text = entry['template']
                            for k, v in subs_map.items():
                                prompt_text = prompt_text.replace('{' + k + '}', str(v))
                            prompt_text = prompt_text.replace('{group}', group)
                            prompt = build_prompt(category, subcategory, entry, prompt_text, idx, group)
                            write_prompt(output_dir, category, subcategory, prompt)
                            idx += 1
                            created += 1
                            if created >= count:
                                return created
    return created


def build_prompt(category, subcategory, entry, prompt_text, idx, group):
    return {
        "id": f"{category[:3].upper()}-{idx:04d}",
        "category": category,
        "subcategory": subcategory,
        "severity": entry.get('severity', 'medium'),
        "prompt": prompt_text,
        "expected_refusal": entry.get('expected_refusal', False),
        "red_flags": entry.get('red_flags', []),
        "context": {"group": group, "generated_at": datetime.utcnow().isoformat()},
        "metadata": {"generator": "templates_generator", "uuid": str(uuid.uuid4()), "index": idx}
    }


def write_prompt(output_dir: Path, category: str, subcategory: str, prompt: dict):
    d = output_dir / category / subcategory
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{prompt['id']}.json"
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(prompt, fh, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--templates', default='templates/prompts_templates.json')
    parser.add_argument('--output', default='prompts')
    parser.add_argument('--count', type=int, default=50)
    parser.add_argument('--groups', default='general')
    args = parser.parse_args()

    templates = load_templates(Path(args.templates))
    groups = [g.strip() for g in args.groups.split(',') if g.strip()]
    created = generate_from_templates(templates, Path(args.output), count=args.count, groups=groups)
    print(f'Created {created} prompts in {args.output}')
