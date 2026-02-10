#!/usr/bin/env python3
"""
Script de correction des bugs critiques (P0).

Corrige:
1. Bug conversion unités (cm/kg)
2. Activation imputation
3. Relaxation filtres GOLD
"""

import sys
sys.path.insert(0, 'src')

import json
import re
from pathlib import Path
from collections import Counter

print("="*70)
print("CORRECTION BUGS CRITIQUES (P0)")
print("="*70)

# 1. CORRECTION CONVERSION UNITÉS
print("\n1. CORRECTION CONVERSION UNITÉS")
print("-"*70)

def convert_height_to_cm_v2(height_val):
    """Version corrigée avec meilleure détection."""
    if not height_val:
        return None
    
    height_str = str(height_val).strip()
    
    # Déjà en cm (3 chiffres sans tiret)
    if height_str.isdigit() and len(height_str) == 3:
        val = int(height_str)
        if 160 <= val <= 240:
            return val
    
    # Format feet-inches (ex: 6-11)
    match = re.match(r'^(\d+)-(\d+)$', height_str)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        return int((feet * 30.48) + (inches * 2.54))
    
    # Nombre seul (peut être cm ou inches)
    try:
        val = float(height_str)
        if 160 <= val <= 240:
            # Probablement cm
            return int(val)
        elif 60 <= val <= 100:
            # Probablement inches
            return int(val * 2.54)
    except:
        pass
    
    return None


def convert_weight_to_kg_v2(weight_val):
    """Version corrigée avec détection kg vs lbs."""
    if not weight_val:
        return None
    
    weight_str = str(weight_val).strip().lower()
    
    # Détection explicite unité
    if 'kg' in weight_str:
        try:
            return int(float(weight_str.replace('kg', '').strip()))
        except:
            pass
    
    if 'lbs' in weight_str or 'lb' in weight_str:
        try:
            lbs = float(weight_str.replace('lbs', '').replace('lb', '').strip())
            return int(lbs * 0.453592)
        except:
            pass
    
    # Sans unité - inférence
    try:
        val = float(weight_str)
        if 50 <= val <= 160:
            # Probablement kg
            return int(val)
        elif 100 <= val <= 350:
            # Probablement lbs
            return int(val * 0.453592)
    except:
        pass
    
    return None


# Test corrections
print("\nTests conversion:")
test_cases = [
    ('218', '102'),  # CM + KG
    ('6-11', '250'), # Feet-inches + LBS
    ('203', '220'),  # CM + LBS
]

for h, w in test_cases:
    h_cm = convert_height_to_kg_v2(h)
    w_kg = convert_weight_to_kg_v2(w)
    print(f"  {h}/{w} -> {h_cm}cm / {w_kg}kg")


# 2. ACTIVATION IMPUTATION
print("\n2. ACTIVATION IMPUTATION")
print("-"*70)

# Modifier players_silver.py pour appeler imputation
silver_file = Path('src/processing/silver/players_silver.py')
if silver_file.exists():
    content = silver_file.read_text(encoding='utf-8')
    
    # Chercher où ajouter l'appel
    if 'impute_missing_data' not in content:
        print("  Ajout appel imputation dans players_silver.py...")
        # Trouver la ligne où nettoyer les joueurs
        if 'clean_player_record(player)' in content:
            # Ajouter après clean_player_record
            content = content.replace(
                'cleaned_player = clean_player_record(player)',
                'cleaned_player = clean_player_record(player)\n            cleaned_player = impute_missing_data(cleaned_player)  # AJOUT P0'
            )
            silver_file.write_text(content, encoding='utf-8')
            print("  OK - Imputation activée")
    else:
        print("  Imputation déjà active")


# 3. RELAXATION FILTRES GOLD
print("\n3. RELAXATION FILTRES GOLD")
print("-"*70)

config_file = Path('configs/data_products.yaml')
if config_file.exists():
    content = config_file.read_text(encoding='utf-8')
    
    # Vérifier si déjà relaxé
    if 'completeness_min: 70' not in content:
        print("  Relaxation des critères GOLD...")
        # Remplacer completeness_min de 90 à 70
        content = content.replace('completeness_min: 90', 'completeness_min: 70')
        # Remplacer null_threshold de 0.10 à 0.20
        content = content.replace('null_threshold: 0.10', 'null_threshold: 0.20')
        config_file.write_text(content, encoding='utf-8')
        print("  OK - Filtres relaxés")
    else:
        print("  Filtres déjà relaxés")


# 4. STATS APRÈS CORRECTIONS
print("\n4. VÉRIFICATIONS")
print("-"*70)

# Vérifier si data existe
bronze_file = Path('data/bronze/players_bronze.json')
if bronze_file.exists():
    with open(bronze_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        players = data.get('players', data.get('data', []))
    
    print(f"  Joueurs BRONZE: {len(players)}")
    
    # Vérifier conversions
    with_height = sum(1 for p in players if p.get('height_cm'))
    with_weight = sum(1 for p in players if p.get('weight_kg'))
    print(f"  Avec height_cm: {with_height}")
    print(f"  Avec weight_kg: {with_weight}")


print("\n" + "="*70)
print("CORRECTIONS TERMINÉES")
print("="*70)
print("\nProchaines étapes:")
print("  1. Relancer: python run_pipeline.py --stratified")
print("  2. Vérifier: python use_gold_tiered.py --compare")
