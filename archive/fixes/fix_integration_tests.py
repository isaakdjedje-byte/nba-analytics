#!/usr/bin/env python3
"""Corrige les tests d'integration"""

# Fix test_catalog_real.py
with open('tests/integration/test_catalog_real.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'with tempfile.TemporaryDirectory() as tmpdir:',
    'with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:'
)

with open('tests/integration/test_catalog_real.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Integration tests corriges:")
print("- test_catalog_real.py: ignore_cleanup_errors=True")
