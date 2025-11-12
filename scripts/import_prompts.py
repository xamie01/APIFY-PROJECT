#!/usr/bin/env python3
"""
Simple importer for Prompts.txt -> prompts/<category>/<subcategory>/*.json

It looks for JSON objects inside the text file and writes them to appropriate folders.
"""
import re
import json
from pathlib import Path
import argparse

JSON_OBJ_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def extract_json_objects(text: str):
    # This is a simple extractor; for robust parsing consider a real parser
    objs = []
    stack = []
    start = None
    for i, ch in enumerate(text):
        if ch == '{':
            if not stack:
                start = i
            stack.append(ch)
        elif ch == '}':
            if stack:
                stack.pop()
                if not stack and start is not None:
                    objs.append(text[start:i+1])
                    start = None
    return objs


def import_prompts(source: Path, output_dir: Path):
    txt = source.read_text(encoding='utf-8')
    objs = extract_json_objects(txt)
    count = 0
    for raw in objs:
        try:
            data = json.loads(raw)
        except Exception:
            continue
        cat = data.get('category', 'uncategorized')
        sub = data.get('subcategory', 'general')
        outdir = output_dir / cat / sub
        outdir.mkdir(parents=True, exist_ok=True)
        id = data.get('id') or f"GEN-{count:04d}"
        fname = outdir / f"{id}.json"
        with open(fname, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        count += 1
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='Prompts.txt')
    parser.add_argument('--output-dir', default='prompts')
    args = parser.parse_args()
    src = Path(args.source)
    out = Path(args.output_dir)
    if not src.exists():
        print('Source not found:', src)
        raise SystemExit(1)
    n = import_prompts(src, out)
    print(f'Imported {n} prompts to {out}')
