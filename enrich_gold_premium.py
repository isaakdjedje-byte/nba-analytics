#!/usr/bin/env python3
"""
Script d'enrichissement ML - Phase 2 GOLD Premium.

Entraîne un modèle K-Means sur GOLD Standard et enrichit GOLD Basic
pour créer GOLD Premium avec métadonnées complètes.
"""

import sys
import json
import pickle
from pathlib import Path
from collections import Counter

# Ajouter src au path
sys.path.insert(0, 'src')

# Import direct sans passer par __init__.py
sys.path.insert(0, 'src/ml/enrichment')
from position_predictor import PositionPredictor, CareerStatusInferencer


def train_position_model():
    """Entraîne le modèle de prédiction de position."""
    print("="*70)
    print("PHASE 2: ENTRAÎNEMENT MODÈLE POSITION")
    print("="*70)
    
    # Charger GOLD Standard (training set)
    print("\n1. Chargement GOLD Standard...")
    with open('data/silver/players_gold_standard/players.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        training_players = data.get('data', [])
    
    print(f"   ✓ {len(training_players)} joueurs chargés")
    
    # Distribution positions
    positions = [p.get('position') for p in training_players if p.get('position')]
    pos_dist = Counter(positions)
    print(f"\n2. Distribution positions:")
    for pos, count in sorted(pos_dist.items(), key=lambda x: -x[1]):
        pct = (count / len(positions)) * 100
        print(f"   {pos:5} - {count:3} joueurs ({pct:5.1f}%)")
    
    # Entraîner modèle
    print("\n3. Entraînement K-Means...")
    predictor = PositionPredictor()
    
    if predictor.train(training_players):
        print(f"   ✓ Modèle entraîné!")
        print(f"   ✓ Accuracy estimée: {predictor.training_stats.get('accuracy_estimate', 0):.1f}%")
        print(f"   ✓ Clusters: {predictor.training_stats.get('n_clusters', 0)}")
        
        # Sauvegarder
        Path('models').mkdir(exist_ok=True)
        predictor.save_model('models/position_predictor.pkl')
        print(f"   ✓ Modèle sauvegardé: models/position_predictor.pkl")
        
        return predictor
    else:
        print("   ❌ Échec entraînement")
        return None


def enrich_gold_basic(predictor):
    """Enrichit GOLD Basic pour créer GOLD Premium."""
    print("\n" + "="*70)
    print("ENRICHISSEMENT GOLD BASIC → GOLD PREMIUM")
    print("="*70)
    
    # Charger GOLD Basic
    print("\n1. Chargement GOLD Basic...")
    with open('data/silver/players_gold_basic/players.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        basic_players = data.get('data', [])
    
    print(f"   ✓ {len(basic_players)} joueurs à enrichir")
    
    # Enrichir chaque joueur
    print("\n2. Enrichissement en cours...")
    enriched_count = 0
    position_predicted = 0
    career_inferred = 0
    
    premium_candidates = []
    
    for i, player in enumerate(basic_players):
        if i % 500 == 0 and i > 0:
            print(f"   Progression: {i}/{len(basic_players)} joueurs traités")
        
        enriched = player.copy()
        fields_added = []
        
        # Prédire position si manquante
        if not enriched.get('position'):
            height = enriched.get('height_cm')
            weight = enriched.get('weight_kg')
            
            if height and weight:
                prediction = predictor.predict(height, weight, confidence_threshold=0.5)
                if prediction:
                    enriched['position'] = prediction['position']
                    enriched['position_confidence'] = prediction['confidence']
                    enriched['position_predicted'] = True
                    fields_added.append('position')
                    position_predicted += 1
        
        # Inférer is_active si manquant
        if enriched.get('is_active') is None:
            from_year = enriched.get('from_year')
            to_year = enriched.get('to_year')
            
            inferencer = CareerStatusInferencer()
            is_active = inferencer.infer(from_year, to_year)
            
            if is_active is not None:
                enriched['is_active'] = is_active
                enriched['is_active_inferred'] = True
                fields_added.append('is_active')
                career_inferred += 1
        
        # Vérifier si joueur qualifié pour Premium (position + is_active)
        if enriched.get('position') and enriched.get('is_active') is not None:
            premium_candidates.append(enriched)
            enriched_count += 1
    
    print(f"\n3. Résultats enrichissement:")
    print(f"   ✓ Positions prédites: {position_predicted}")
    print(f"   ✓ Statuts inférés: {career_inferred}")
    print(f"   ✓ Joueurs Premium: {len(premium_candidates)}")
    
    return premium_candidates


def save_gold_premium(players):
    """Sauvegarde GOLD Premium."""
    print("\n" + "="*70)
    print("SAUVEGARDE GOLD PREMIUM")
    print("="*70)
    
    output_path = 'data/silver/players_gold_premium/players.json'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'data': players}, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Sauvegardé: {output_path}")
    print(f"✓ {len(players)} joueurs GOLD Premium")
    
    # Stats
    positions = [p.get('position') for p in players if p.get('position')]
    pos_dist = Counter(positions)
    print(f"\nDistribution positions:")
    for pos, count in sorted(pos_dist.items(), key=lambda x: -x[1])[:5]:
        print(f"  {pos}: {count} joueurs")


def main():
    print("NBA ANALYTICS - PHASE 2: ENRICHISSEMENT ML")
    print("="*70)
    
    # Étape 1: Entraîner modèle
    predictor = train_position_model()
    if not predictor:
        print("\n❌ Arrêt - Impossible d'entraîner le modèle")
        return 1
    
    # Étape 2: Enrichir GOLD Basic
    premium_players = enrich_gold_basic(predictor)
    
    # Étape 3: Sauvegarder
    save_gold_premium(premium_players)
    
    # Résumé final
    print("\n" + "="*70)
    print("RÉSUMÉ FINAL - GOLD TIERED")
    print("="*70)
    print("\nAvant enrichissement:")
    print("  GOLD Premium: 0 joueurs")
    print("\nAprès enrichissement:")
    print(f"  GOLD Premium: {len(premium_players)} joueurs (+∞%)")
    print("\n✅ Phase 2 complétée avec succès!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
