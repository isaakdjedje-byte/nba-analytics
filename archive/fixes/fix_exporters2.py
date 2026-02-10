#!/usr/bin/env python3
"""Corrige les __init__ des classes enfants"""

with open('nba/reporting/exporters.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplace les __init__ des classes enfants
replacements = [
    # ParquetExporter
    ('class ParquetExporter(BaseExporter):\n    """Exporteur Parquet professionnel"""\n    \n    def __init__(self):\n        super().__init__("parquet")',
     'class ParquetExporter(BaseExporter):\n    """Exporteur Parquet professionnel"""\n    \n    def __init__(self, gold_path=None):\n        super().__init__("parquet", gold_path)'),
    
    # CSVExporter
    ('class CSVExporter(BaseExporter):\n    """Exporteur CSV pour compatibilite"""\n    \n    def __init__(self):\n        super().__init__("csv")',
     'class CSVExporter(BaseExporter):\n    """Exporteur CSV pour compatibilite"""\n    \n    def __init__(self, gold_path=None):\n        super().__init__("csv", gold_path)'),
    
    # JSONExporter
    ('class JSONExporter(BaseExporter):\n    """Exporteur JSON pour APIs"""\n    \n    def __init__(self):\n        super().__init__("json")',
     'class JSONExporter(BaseExporter):\n    """Exporteur JSON pour APIs"""\n    \n    def __init__(self, gold_path=None):\n        super().__init__("json", gold_path)'),
    
    # DeltaExporter
    ('class DeltaExporter(BaseExporter):\n    """Exporteur Delta Lake (si disponible)"""\n    \n    def __init__(self):\n        super().__init__("delta")',
     'class DeltaExporter(BaseExporter):\n    """Exporteur Delta Lake (si disponible)"""\n    \n    def __init__(self, gold_path=None):\n        super().__init__("delta", gold_path)'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open('nba/reporting/exporters.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Classes enfants corrigees:")
print("- ParquetExporter(gold_path=None)")
print("- CSVExporter(gold_path=None)")
print("- JSONExporter(gold_path=None)")
print("- DeltaExporter(gold_path=None)")
