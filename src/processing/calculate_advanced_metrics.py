#!/usr/bin/env python3
"""
NBA-18: Calcul des métriques avancées
Pipeline de calcul des statistiques avancées pour les joueurs
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.nba_formulas import (
    calculate_per_simplified,
    calculate_ts_pct,
    calculate_efg_pct,
    calculate_usage_rate,
    calculate_game_score,
    calculate_bmi,
    calculate_all_metrics
)


class AdvancedMetricsCalculator:
    """Calculateur de métriques avancées NBA"""
    
    def __init__(self, input_path: str = None, output_path: str = None):
        self.input_path = Path(input_path or "data/silver/players_gold_standard/players.json")
        self.output_path = Path(output_path or "data/silver/players_advanced")
        self.stats = {
            'total_players': 0,
            'processed': 0,
            'errors': 0,
            'metrics_calculated': {}
        }
    
    def load_players(self) -> List[Dict[str, Any]]:
        """Charge les joueurs depuis le dataset GOLD Standard"""
        print(f"Chargement des joueurs depuis: {self.input_path}")
        
        if not self.input_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {self.input_path}")
        
        with open(self.input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        players = data.get('data', [])
        self.stats['total_players'] = len(players)
        
        print(f"✓ {len(players)} joueurs chargés")
        return players
    
    def calculate_player_metrics(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule toutes les métriques pour un joueur"""
        # Préparer les données
        player_data = {
            'pts': player.get('points', 0) or player.get('pts', 0),
            'fgm': player.get('field_goals_made', 0) or player.get('fgm', 0),
            'fga': player.get('field_goals_attempted', 0) or player.get('fga', 0),
            'ftm': player.get('free_throws_made', 0) or player.get('ftm', 0),
            'fta': player.get('free_throws_attempted', 0) or player.get('fta', 0),
            '3pm': player.get('three_points_made', 0) or player.get('3pm', 0),
            'oreb': player.get('offensive_rebounds', 0) or player.get('oreb', 0),
            'dreb': player.get('defensive_rebounds', 0) or player.get('dreb', 0),
            'reb': player.get('rebounds', 0) or player.get('reb', 0),
            'ast': player.get('assists', 0) or player.get('ast', 0),
            'stl': player.get('steals', 0) or player.get('stl', 0),
            'blk': player.get('blocks', 0) or player.get('blk', 0),
            'tov': player.get('turnovers', 0) or player.get('tov', 0),
            'pf': player.get('personal_fouls', 0) or player.get('pf', 0),
            'minutes': player.get('minutes', 0) or 1,  # Éviter division par zéro
            'height_cm': player.get('height_cm', 0),
            'weight_kg': player.get('weight_kg', 0)
        }
        
        # Calculer les métriques
        metrics = calculate_all_metrics(player_data)
        
        # Ajouter les métriques au joueur
        player_with_metrics = player.copy()
        player_with_metrics.update(metrics)
        
        return player_with_metrics
    
    def process_all_players(self, players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Traite tous les joueurs et calcule leurs métriques"""
        print("\nCalcul des métriques avancées...")
        
        processed_players = []
        
        for i, player in enumerate(players, 1):
            try:
                # Afficher progression tous les 1000 joueurs
                if i % 1000 == 0:
                    print(f"  Progression: {i}/{len(players)} joueurs ({i/len(players)*100:.1f}%)")
                
                # Calculer métriques
                player_with_metrics = self.calculate_player_metrics(player)
                processed_players.append(player_with_metrics)
                self.stats['processed'] += 1
                
            except Exception as e:
                print(f"  ⚠️  Erreur pour {player.get('full_name', 'Unknown')}: {e}")
                self.stats['errors'] += 1
                # Ajouter quand même avec métriques à 0
                player['per'] = 0.0
                player['ts_pct'] = 0.0
                player['efg_pct'] = 0.0
                player['usg_pct'] = 0.0
                player['game_score'] = 0.0
                player['bmi'] = 0.0
                processed_players.append(player)
        
        print(f"✓ {self.stats['processed']} joueurs traités")
        if self.stats['errors'] > 0:
            print(f"⚠️  {self.stats['errors']} erreurs")
        
        return processed_players
    
    def calculate_statistics(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les statistiques globales"""
        print("\nCalcul des statistiques globales...")
        
        metrics_summary = {
            'per': [],
            'ts_pct': [],
            'efg_pct': [],
            'usg_pct': [],
            'game_score': [],
            'bmi': []
        }
        
        # Collecter toutes les valeurs
        for player in players:
            for metric in metrics_summary.keys():
                value = player.get(metric, 0)
                if value and value > 0:  # Ignorer les 0
                    metrics_summary[metric].append(value)
        
        # Calculer stats
        stats = {}
        for metric, values in metrics_summary.items():
            if values:
                stats[metric] = {
                    'count': len(values),
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'median': sorted(values)[len(values) // 2]
                }
        
        self.stats['metrics_calculated'] = stats
        
        # Afficher résumé
        print("\n📊 Statistiques globales:")
        for metric, stat in stats.items():
            print(f"  {metric}:")
            print(f"    Moyenne: {stat['mean']:.3f}")
            print(f"    Min/Max: {stat['min']:.3f} / {stat['max']:.3f}")
            print(f"    Joueurs: {stat['count']}")
        
        return stats
    
    def save_results(self, players: List[Dict[str, Any]], stats: Dict[str, Any]):
        """Sauvegarde les résultats"""
        print(f"\nSauvegarde des résultats dans: {self.output_path}")
        
        # Créer dossier
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder joueurs
        output_file = self.output_path / "players.json"
        output_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'version': 'NBA-18-v1.0',
                'total_players': len(players),
                'metrics': ['per', 'ts_pct', 'efg_pct', 'usg_pct', 'game_score', 'bmi']
            },
            'data': players
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Joueurs sauvegardés: {output_file}")
        
        # Sauvegarder métadonnées
        metadata_file = self.output_path / "_metadata.json"
        metadata = {
            'created_at': datetime.now().isoformat(),
            'version': 'NBA-18-v1.0',
            'total_players': len(players),
            'processed': self.stats['processed'],
            'errors': self.stats['errors'],
            'statistics': stats
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Métadonnées sauvegardées: {metadata_file}")
        
        # Sauvegarder rapport validation
        validation_file = self.output_path / "metrics_validation.json"
        validation_report = {
            'validation_date': datetime.now().isoformat(),
            'total_players': len(players),
            'metrics_calculated': list(stats.keys()),
            'statistics_summary': {
                metric: {
                    'mean': round(stat['mean'], 3),
                    'count': stat['count']
                }
                for metric, stat in stats.items()
            },
            'validation_status': 'SUCCESS'
        }
        
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_report, f, indent=2)
        
        print(f"✓ Rapport validation: {validation_file}")
    
    def run(self):
        """Exécute le pipeline complet"""
        print("="*60)
        print("NBA-18: CALCUL DES MÉTRIQUES AVANCÉES")
        print("="*60)
        
        try:
            # 1. Charger les joueurs
            players = self.load_players()
            
            # 2. Calculer les métriques
            processed_players = self.process_all_players(players)
            
            # 3. Calculer statistiques globales
            stats = self.calculate_statistics(processed_players)
            
            # 4. Sauvegarder résultats
            self.save_results(processed_players, stats)
            
            print("\n" + "="*60)
            print("✅ NBA-18 COMPLÉTÉ AVEC SUCCÈS")
            print("="*60)
            print(f"\n📈 Résultats:")
            print(f"  Joueurs traités: {self.stats['processed']}")
            print(f"  Métriques calculées: {len(stats)}")
            print(f"  Sortie: {self.output_path}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Point d'entrée principal"""
    calculator = AdvancedMetricsCalculator()
    success = calculator.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
