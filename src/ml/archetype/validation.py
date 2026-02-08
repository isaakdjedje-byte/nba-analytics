#!/usr/bin/env python3
"""
NBA-23: Validation des archétypes avec ground truth

Valide la qualité du clustering en comparant avec des joueurs connus.
"""

import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Résultat de la validation d'un joueur"""
    player_name: str
    expected_archetype: str
    actual_archetype: str
    is_correct: bool
    confidence: float
    per: float


class ArchetypeValidator:
    """
    Valide la qualité des clusters avec ground truth partiel.
    
    Compare les archétypes prédits avec des classifications manuelles
    de joueurs bien connus pour évaluer la précision du système.
    """
    
    # Ground truth: Joueurs connus et leurs archétypes attendus
    # Basé sur l'observation des carrières et des styles de jeu
    GROUND_TRUTH = {
        # === ELITE ===
        'LeBron James': 'ELITE_TWO_WAY',
        'Stephen Curry': 'ELITE_SCORER',
        'Kevin Durant': 'ELITE_SCORER',
        'Giannis Antetokounmpo': 'ELITE_TWO_WAY',
        'Joel Embiid': 'ELITE_SCORER',
        'Nikola Jokic': 'ELITE_PLAYMAKER',
        'Luka Doncic': 'ELITE_PLAYMAKER',
        'Kawhi Leonard': 'ELITE_TWO_WAY',
        'Jimmy Butler': 'ELITE_TWO_WAY',
        'Chris Paul': 'ELITE_PLAYMAKER',
        'Trae Young': 'ELITE_PLAYMAKER',
        'Tyrese Haliburton': 'ELITE_PLAYMAKER',
        'Rudy Gobert': 'ELITE_BIG',
        'Brook Lopez': 'ELITE_BIG',
        'Myles Turner': 'ELITE_BIG',
        
        # === STARTER ===
        'Bradley Beal': 'STARTER_OFFENSIVE',
        'Zach LaVine': 'STARTER_OFFENSIVE',
        'DeMar DeRozan': 'STARTER_OFFENSIVE',
        'Jaylen Brown': 'STARTER_BALANCED',
        'Paul George': 'STARTER_BALANCED',
        'Mikal Bridges': 'STARTER_BALANCED',
        'Alex Caruso': 'STARTER_DEFENSIVE',
        'Jrue Holiday': 'STARTER_DEFENSIVE',
        'Dyson Daniels': 'STARTER_DEFENSIVE',
        
        # === ROLE PLAYER ===
        'Dorian Finney-Smith': 'ROLE_3_AND_D',
        'OG Anunoby': 'ROLE_3_AND_D',
        'Derrick Jones Jr': 'ROLE_3_AND_D',
        'Montrezl Harrell': 'ROLE_ENERGY_BIG',
        'Isaiah Stewart': 'ROLE_ENERGY_BIG',
        'Naz Reid': 'ROLE_ENERGY_BIG',
        "Day'Ron Sharpe": 'ROLE_ENERGY_BIG',
        'Matisse Thybulle': 'ROLE_DEFENSIVE',
        'Kris Dunn': 'ROLE_DEFENSIVE',
        'Doug McDermott': 'ROLE_SHOOTER',
        'Patty Mills': 'ROLE_SHOOTER',
        'Royce ONeale': 'ROLE_3_AND_D',
        'Josh Hart': 'ROLE_3_AND_D',
        'Larry Nance Jr': 'ROLE_ENERGY_BIG',
        
        # === BENCH ===
        'Jarred Vanderbilt': 'BENCH_ENERGY',
        'Trendon Watford': 'BENCH_ENERGY',
        'Cole Swider': 'BENCH_SHOOTER',
    }
    
    def __init__(self):
        self.results = []
        self.errors = []
    
    def validate(self, df_archetypes: pd.DataFrame) -> Dict:
        """
        Valide le clustering contre le ground truth.
        
        Args:
            df_archetypes: DataFrame avec colonnes 'player_name', 'archetype_id', 
                          'max_probability', 'per'
            
        Returns:
            Dict avec métriques de validation
        """
        self.results = []
        self.errors = []
        
        correct = 0
        total = 0
        
        for player_name, expected_arch in self.GROUND_TRUTH.items():
            # Cherche le joueur dans les données
            player_data = df_archetypes[df_archetypes['player_name'] == player_name]
            
            if len(player_data) == 0:
                # Joueur non trouvé
                self.errors.append({
                    'player': player_name,
                    'error': 'Joueur non trouvé dans les données clusterisées',
                    'expected': expected_arch
                })
                continue
            
            actual_arch = player_data['archetype_id'].iloc[0]
            confidence = player_data.get('max_probability', pd.Series([0.5])).iloc[0]
            per = player_data.get('per', pd.Series([15.0])).iloc[0]
            
            is_correct = (actual_arch == expected_arch)
            
            if is_correct:
                correct += 1
            
            total += 1
            
            self.results.append(ValidationResult(
                player_name=player_name,
                expected_archetype=expected_arch,
                actual_archetype=actual_arch,
                is_correct=is_correct,
                confidence=confidence,
                per=per
            ))
        
        # Calcule les métriques
        accuracy = correct / total if total > 0 else 0
        
        # Analyse par niveau
        level_accuracy = self._calculate_level_accuracy()
        
        return {
            'accuracy': accuracy,
            'total_checked': total,
            'correct_matches': correct,
            'errors': self.errors,
            'level_accuracy': level_accuracy,
            'is_valid': accuracy >= 0.6,  # Seuil de validation: 60%
            'detailed_results': self.results
        }
    
    def _calculate_level_accuracy(self) -> Dict[str, float]:
        """Calcule l'accuracy par niveau (ELITE, STARTER, etc.)."""
        level_stats = {}
        
        for result in self.results:
            # Extrait le niveau de l'expected archetype
            expected_level = result.expected_archetype.split('_')[0]
            
            if expected_level not in level_stats:
                level_stats[expected_level] = {'correct': 0, 'total': 0}
            
            level_stats[expected_level]['total'] += 1
            if result.is_correct:
                level_stats[expected_level]['correct'] += 1
        
        # Calcule les pourcentages
        level_accuracy = {}
        for level, stats in level_stats.items():
            level_accuracy[level] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        
        return level_accuracy
    
    def get_error_analysis(self) -> pd.DataFrame:
        """Retourne une analyse détaillée des erreurs."""
        errors = [r for r in self.results if not r.is_correct]
        
        if not errors:
            return pd.DataFrame()
        
        return pd.DataFrame([
            {
                'player': e.player_name,
                'expected': e.expected_archetype,
                'actual': e.actual_archetype,
                'confidence': e.confidence,
                'per': e.per
            }
            for e in errors
        ])
    
    def get_summary_report(self) -> str:
        """Génère un rapport textuel de la validation."""
        if not self.results:
            return "Aucun résultat de validation disponible."
        
        report = []
        report.append("=" * 70)
        report.append("RAPPORT DE VALIDATION NBA-23")
        report.append("=" * 70)
        
        correct = sum(1 for r in self.results if r.is_correct)
        total = len(self.results)
        accuracy = correct / total * 100
        
        report.append(f"\nAccuracy globale: {accuracy:.1f}% ({correct}/{total})")
        report.append(f"Statut: {'✓ VALIDÉ' if accuracy >= 60 else '✗ ÉCHEC'}")
        
        # Par niveau
        report.append("\nAccuracy par niveau:")
        level_acc = self._calculate_level_accuracy()
        for level, acc in level_acc.items():
            report.append(f"  {level}: {acc*100:.1f}%")
        
        # Erreurs
        errors = self.get_error_analysis()
        if not errors.empty:
            report.append(f"\nErreurs ({len(errors)} joueurs):")
            for _, row in errors.head(10).iterrows():
                report.append(f"  - {row['player']}: attendu {row['expected']}, "
                            f"obtenu {row['actual']} (conf: {row['confidence']:.2%})")
        
        report.append("=" * 70)
        
        return '\n'.join(report)
    
    def export_ground_truth_template(self) -> pd.DataFrame:
        """
        Exporte un template pour ajouter plus de ground truth.
        """
        return pd.DataFrame([
            {'player_name': name, 'expected_archetype': arch}
            for name, arch in self.GROUND_TRUTH.items()
        ])


def quick_validation(df_archetypes: pd.DataFrame) -> bool:
    """
    Fonction utilitaire pour validation rapide.
    
    Returns:
        True si le clustering est validé (accuracy >= 60%)
    """
    validator = ArchetypeValidator()
    result = validator.validate(df_archetypes)
    
    print(validator.get_summary_report())
    
    return result['is_valid']


if __name__ == "__main__":
    print("NBA-23 Archetype Validator")
    print("=" * 60)
    
    validator = ArchetypeValidator()
    
    print(f"\nGround truth défini: {len(validator.GROUND_TRUTH)} joueurs")
    
    # Affiche la répartition
    levels = {}
    for arch in validator.GROUND_TRUTH.values():
        level = arch.split('_')[0]
        levels[level] = levels.get(level, 0) + 1
    
    print("\nRépartition par niveau:")
    for level, count in levels.items():
        print(f"  {level}: {count} joueurs")
    
    print("\nPour tester la validation:")
    print(">>> from src.ml.archetype.validation import quick_validation")
    print(">>> is_valid = quick_validation(df_archetypes)")
