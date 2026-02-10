#!/usr/bin/env python3
"""Corrige les tests DataCatalog pour Windows"""

with open('tests/unit/test_reporting.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplace les with tempfile.TemporaryDirectory() par ignore_cleanup_errors
# C'est un paramètre disponible dans Python 3.10+
content = content.replace(
    'with tempfile.TemporaryDirectory() as tmpdir:',
    'with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:'
)

with open('tests/unit/test_reporting.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Tests DataCatalog corriges:")
print("- ignore_cleanup_errors=True pour Windows")
