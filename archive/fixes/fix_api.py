#!/usr/bin/env python3
"""Corrige le modèle API DatasetInfo"""

with open('nba/api/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Corrige DatasetInfo pour accepter Any
content = content.replace(
    'last_updated: Optional[str] = None',
    'last_updated: Optional[Any] = None'
)

# Ajoute import Any si pas déjà là
if 'from typing import' in content and 'Any' not in content:
    content = content.replace(
        'from typing import Optional, List',
        'from typing import Optional, List, Any'
    )

with open('nba/api/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("API corrigée:")
print("- last_updated: Optional[Any] au lieu de str")
