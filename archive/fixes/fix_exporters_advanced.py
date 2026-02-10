#!/usr/bin/env python3
"""Corrige test_exporters_advanced.py pour utiliser gold_path"""

with open('tests/unit/test_exporters_advanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplace les instanciations d'exporters
replacements = [
    ('exporter = ParquetExporter()', 'exporter = ParquetExporter(gold_path=Path(tmpdir))'),
    ('exporter = CSVExporter()', 'exporter = CSVExporter(gold_path=Path(tmpdir))'),
    ('exporter = JSONExporter()', 'exporter = JSONExporter(gold_path=Path(tmpdir))'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Ajoute ignore_cleanup_errors pour Windows
content = content.replace(
    'with tempfile.TemporaryDirectory() as tmpdir:',
    'with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:'
)

with open('tests/unit/test_exporters_advanced.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("test_exporters_advanced.py corrige:")
print("- gold_path passe aux exporters")
print("- ignore_cleanup_errors pour Windows")
