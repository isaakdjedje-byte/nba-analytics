#!/usr/bin/env python3
"""
Phase 3 - Création GOLD Premium Elite.

Filtre les prédictions avec haute confiance (> 70%)
pour créer un dataset GOLD Premium de qualité supérieure.
"""

import sys
import json
from pathlib import Path
from collections import Counter

sys.path.insert(0, 'src')
sys.path.insert(0, 'src/ml/enrichment')

from position_predictor import PositionPredictor
from advanced_position_predictor import AdvancedPositionPredictor


def create_premium_elite(min_confidence=0.70):
    """Crée GOLD Premium Elite avec filtrage haute confiance."""
    print("="*70)
    print(f"PHASE 3: GOLD PREMIUM ELITE (confiance > {min_confidence:.0%})")
    print("="*70)
    
    # Charger modèles
    print("\n1. Chargement modèles...")
    
    # K-Means
    km = PositionPredictor('models/position_predictor.pkl')
    print(f"   K-Means chargé ({km.training_stats.get('accuracy_estimate', 0):.1f}%)")
    
    # Random Forest
    rf = AdvancedPositionPredictor('models/position_predictor_rf.pkl')
    print(f"   Random Forest chargé ({rf.training_stats.get('accuracy', 0):.1f}%)")
    
    # Charger GOLD Basic
    print("\n2. Chargement GOLD Basic...")
    with open('data/silver/players_gold_basic/players.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        basic_players = data.get('data', [])
    
    print(f"   {len(basic_players)} joueurs à enrichir")
    
    # Enrichir avec filtrage
    print(f"\n3. Enrichissement avec filtre confiance > {min_confidence:.0%}...")
    
    elite_players = []
    high_confidence_count = 0
    medium_confidence_count = 0
    low_confidence_count = 0
    
    for i, player in enumerate(basic_players):
        if i % 500 == 0 and i > 0:
            print(f"   Progression: {i}/{len(basic_players)}")
        
        enriched = player.copy()
        
        # Prédire avec Random Forest (meilleures probabilités)
        height = enriched.get('height_cm')
        weight = enriched.get('weight_kg')
        
        if height and weight and not enriched.get('position'):
            rf_result = rf.predict(height, weight)
            
            if rf_result:
                confidence = rf_result['confidence']
                
                # Catégoriser par confiance
                if confidence >= min_confidence:
                    enriched['position'] = rf_result['position']
                    enriched['position_confidence'] = confidence
                    enriched['position_predicted'] = True
                    enriched['position_method'] = 'random_forest'
                    high_confidence_count += 1
                elif confidence >= 0.5:
                    enriched['position'] = rf_result['position']
                    enriched['position_confidence'] = confidence
                    enriched['position_predicted'] = True
                    enriched['position_method'] = 'random_forest_low_conf'
                    medium_confidence_count += 1
                else:
                    # Faible confiance: pas de prédiction
                    enriched['position'] = None
                    enriched['position_confidence'] = confidence
                    low_confidence_count += 1
                
                # Ajouter toutes les probabilités pour analyse
                enriched['position_probabilities'] = rf_result['all_positions']
        
        # Inférer is_active
        if enriched.get('is_active') is None:
            from_year = enriched.get('from_year')
            to_year = enriched.get('to_year')
            
            from position_predictor import CareerStatusInferencer
            inferencer = CareerStatusInferencer()
            is_active = inferencer.infer(from_year, to_year)
            
            if is_active is not None:
                enriched['is_active'] = is_active
                enriched['is_active_inferred'] = True
        
        # Qualifier pour Elite: position avec haute confiance + is_active
        if (enriched.get('position') and 
            enriched.get('position_confidence', 0) >= min_confidence and
            enriched.get('is_active') is not None):
            elite_players.append(enriched)
    
    print(f"\n4. Résultats filtrage:")
    print(f"   Haute confiance (>={min_confidence:.0%}): {high_confidence_count}")
    print(f"   Moyenne confiance (50-70%): {medium_confidence_count}")
    print(f"   Faible confiance (<50%): {low_confidence_count}")
    print(f"   Joueurs Elite qualifiés: {len(elite_players)}")
    
    # Sauvegarder
    print("\n5. Sauvegarde GOLD Premium Elite...")
    output_path = 'data/silver/players_gold_premium_elite/players.json'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'data': elite_players}, f, indent=2, ensure_ascii=False)
    
    print(f"   OK - {len(elite_players)} joueurs sauvegardés")
    print(f"   Chemin: {output_path}")
    
    # Stats
    if elite_players:
        positions = [p.get('position') for p in elite_players if p.get('position')]
        pos_dist = Counter(positions)
        
        print(f"\n6. Distribution positions (Elite):")
        for pos, count in sorted(pos_dist.items(), key=lambda x: -x[1]):
            pct = (count / len(elite_players)) * 100
            print(f"   {pos:5}: {count:4} joueurs ({pct:5.1f}%)")
        
        # Confiance moyenne
        avg_conf = sum(p.get('position_confidence', 0) for p in elite_players) / len(elite_players)
        print(f"\n   Confiance moyenne: {avg_conf:.1%}")
    
    return elite_players


def compare_premium_versions():
    """Compare les différentes versions de GOLD Premium."""
    print("\n" + "="*70)
    print("COMPARAISON VERSIONS GOLD PREMIUM")
    print("="*70)
    
    versions = {
        'Phase 2 (tous)': 'data/silver/players_gold_premium/players.json',
        'Phase 3 (Elite)': 'data/silver/players_gold_premium_elite/players.json'
    }
    
    print(f"\n{'Version':<20} {'Joueurs':>10} {'Qualité':>15}")
    print("-"*50)
    
    for name, path in versions.items():
        if Path(path).exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                players = data.get('data', [])
            
            # Calculer qualité moyenne (confiance)
            if players and 'position_confidence' in players[0]:
                avg_quality = sum(p.get('position_confidence', 0) for p in players) / len(players)
                quality_str = f"{avg_quality:.1%}"
            else:
                quality_str = "N/A"
            
            print(f"{name:<20} {len(players):>10} {quality_str:>15}")
        else:
            print(f"{name:<20} {'N/A':>10} {'N/A':>15}")
    
    print("-"*50)


def main():
    print("NBA ANALYTICS - PHASE 3: GOLD PREMIUM ELITE")
    print("="*70)
    
    # Créer Elite avec seuil 70%
    elite_players = create_premium_elite(min_confidence=0.70)
    
    # Comparer versions
    compare_premium_versions()
    
    # Résumé final
    print("\n" + "="*70)
    print("RÉSUMÉ PHASE 3")
    print("="*70)
    print(f"\n✅ GOLD Premium Elite créé: {len(elite_players)} joueurs")
    print(f"✅ Filtrage: confiance > 70% uniquement")
    print(f"✅ Qualité supérieure: données fiables pour ML production")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
