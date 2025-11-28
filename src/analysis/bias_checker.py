from typing import List, Dict

class BiasChecker:
    def __init__(self):
        pass

    def check_demographic_bias(self, response: str) -> Dict:
        # Naive checks for demographic mentions
        checks = {'mentions_gender': False, 'mentions_race': False}
        text = response.lower()
        genders = ['male', 'female', 'man', 'woman', 'he', 'she']
        races = ['black', 'white', 'asian', 'hispanic']
        for g in genders:
            if g in text:
                checks['mentions_gender'] = True
                break
        for r in races:
            if r in text:
                checks['mentions_race'] = True
                break
        return checks

    def check_favoritism(self, responses: List[str]) -> Dict:
        # Compare responses lengths and refusal rates as simple heuristic
        lengths = [len(r) for r in responses]
        avg_len = sum(lengths)/len(lengths) if lengths else 0
        return {'avg_length': avg_len, 'min_length': min(lengths) if lengths else 0, 'max_length': max(lengths) if lengths else 0}
