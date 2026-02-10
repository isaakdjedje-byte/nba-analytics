#!/usr/bin/env python3
"""Corrige les tests pour utiliser gold_path configurable"""

# Lecture du fichier test_reporting.py
with open('tests/unit/test_reporting.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern de correction pour chaque test exporter
# Remplace: exporter = ParquetExporter()
# Par: exporter = ParquetExporter(gold_path=Path(tmpdir))

replacements = [
    ('exporter = ParquetExporter()', 'exporter = ParquetExporter(gold_path=Path(tmpdir))'),
    ('exporter = CSVExporter()', 'exporter = CSVExporter(gold_path=Path(tmpdir))'),
    ('exporter = JSONExporter()', 'exporter = JSONExporter(gold_path=Path(tmpdir))'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Écriture
with open('tests/unit/test_reporting.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Tests corriges:")
print("- ParquetExporter utilise gold_path=Path(tmpdir)")
print("- CSVExporter utilise gold_path=Path(tmpdir)")
print("- JSONExporter utilise gold_path=Path(tmpdir)")
