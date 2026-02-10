#!/usr/bin/env python3
"""Script pour corriger les exporters"""

with open('nba/reporting/exporters.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Modification 1: Ajouter gold_path au __init__
old_init = '''    def __init__(self, format_name: str):
        self.format_name = format_name'''

new_init = '''    def __init__(self, format_name: str, gold_path=None):
        self.format_name = format_name
        self.gold_path = gold_path or Path("data/gold")'''

content = content.replace(old_init, new_init)

# Modification 2: Utiliser self.gold_path
old_load = '''    def _load_dataset(self, dataset: str) -> pd.DataFrame:
        """Charge un dataset depuis data/gold/"""
        gold_path = Path("data/gold")'''

new_load = '''    def _load_dataset(self, dataset: str) -> pd.DataFrame:
        """Charge un dataset depuis gold_path"""
        gold_path = self.gold_path'''

content = content.replace(old_load, new_load)

with open('nba/reporting/exporters.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Corrections appliquees:")
print("1. gold_path configurable dans __init__")
print("2. _load_dataset utilise self.gold_path")
