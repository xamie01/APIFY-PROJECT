import json
from typing import List, Dict

class Reporter:
    def __init__(self):
        pass

    def generate_summary(self, results: List[Dict]) -> Dict:
        total = len(results)
        passes = 0
        for r in results:
            # naive: pass if any model returned text
            ok = any('response' in x and x['response'] for x in r.get('results', []))
            if ok:
                passes += 1
        return {'total_prompts': total, 'passes': passes, 'fails': total - passes}

    def export_json(self, data: Dict) -> str:
        return json.dumps(data, indent=2)

    def export_csv(self, data: Dict) -> str:
        # Minimal CSV exporter for summary
        keys = sorted(data.keys())
        header = ','.join(keys)
        row = ','.join(str(data[k]) for k in keys)
        return header + '\n' + row
