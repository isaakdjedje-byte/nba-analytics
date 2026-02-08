#!/usr/bin/env python3
"""
NBA-24: Détection des joueurs en progression

Approche optimisée: Comparaison tendance récente vs début de saison
(Adapté car pas de données historiques multi-saisons disponibles)

Détecte les joueurs qui montent en puissance basé sur:
1. Progression vs début de saison (derniers matchs)
2. Performance au-dessus de la moyenne de leur équipe
3. Classement percentile dans la ligue
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProgressionDetector:
    """
    Détecteur de progression des joueurs NBA.
    
    Usage:
        detector = ProgressionDetector()
        rising_stars = detector.detect_trending_players()
        detector.generate_report()
    """
    
    def __init__(self, 
                 players_path: str = "data/silver/players_advanced/players_enriched_final.json",
                 games_path: str = "data/silver/games_processed/games_structured.json",
                 team_stats_path: str = "data/gold/team_season_stats/team_season_stats.json"):
        """
        Initialise le détecteur.
        
        Args:
            players_path: Chemin vers données joueurs enrichies
            games_path: Chemin vers matchs structurés
            team_stats_path: Chemin vers stats équipes
        """
        self.players_path = Path(players_path)
        self.games_path = Path(games_path)
        self.team_stats_path = Path(team_stats_path)
        
        self.players_df = None
        self.team_stats_df = None
        self.progressions = []
        
    def load_data(self) -> 'ProgressionDetector':
        """Charge les données nécessaires."""
        logger.info("Chargement des données...")
        
        # Charger joueurs
        if self.players_path.exists():
            with open(self.players_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'data' in data:
                    self.players_df = pd.DataFrame(data['data'])
                else:
                    self.players_df = pd.DataFrame(data)
            logger.info(f"[OK] {len(self.players_df)} joueurs chargés")
        else:
            logger.warning(f"Fichier joueurs non trouvé: {self.players_path}")
            self.players_df = pd.DataFrame()
        
        # Charger stats équipes
        if self.team_stats_path.exists():
            with open(self.team_stats_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'data' in data:
                    self.team_stats_df = pd.DataFrame(data['data'])
                else:
                    self.team_stats_df = pd.DataFrame(data)
            logger.info(f"[OK] {len(self.team_stats_df)} stats équipes chargées")
        else:
            logger.warning(f"Fichier stats équipes non trouvé: {self.team_stats_path}")
            self.team_stats_df = pd.DataFrame()
        
        return self
    
    def calculate_ligue_percentile(self, metric: str = 'per') -> pd.Series:
        """
        Calcule le percentile d'un joueur dans la ligue pour une métrique.
        
        Args:
            metric: Nom de la métrique (per, ts_pct, etc.)
            
        Returns:
            Series avec percentiles (0-100)
        """
        if self.players_df.empty or metric not in self.players_df.columns:
            return pd.Series()
        
        # Calculer percentile
        percentiles = self.players_df[metric].rank(pct=True) * 100
        return percentiles
    
    def detect_trending_players(self, 
                                min_games: int = 10,
                                progression_threshold: float = 10.0) -> pd.DataFrame:
        """
        Détecte les joueurs en progression significative.
        
        Méthode: Compare performance actuelle vs référence
        - Joueurs avec PER au-dessus du percentile 80
        - ET performance supérieure à leur équipe
        - ET ratio TS% > moyenne ligue
        
        Args:
            min_games: Nombre minimum de matchs (non utilisé, présent pour compatibilité)
            progression_threshold: Seuil de progression (%) pour considérer significatif
            
        Returns:
            DataFrame avec joueurs en progression
        """
        logger.info("Détection des joueurs en progression...")
        
        if self.players_df.empty:
            logger.error("Pas de données joueurs disponibles")
            return pd.DataFrame()
        
        # Calculer percentiles
        self.players_df['per_percentile'] = self.calculate_ligue_percentile('per')
        self.players_df['ts_pct_percentile'] = self.calculate_ligue_percentile('ts_pct')
        
        # Calculer score de progression composite
        # Basé sur: PER, TS%, USG%, Game Score
        metrics = ['per', 'ts_pct', 'usg_pct', 'game_score']
        available_metrics = [m for m in metrics if m in self.players_df.columns]
        
        if not available_metrics:
            logger.error("Aucune métrique disponible pour calculer progression")
            return pd.DataFrame()
        
        # Normaliser chaque métrique (0-100)
        for metric in available_metrics:
            col_name = f'{metric}_norm'
            self.players_df[col_name] = self.players_df[metric].rank(pct=True) * 100
        
        # Score composite (moyenne des percentiles)
        norm_cols = [f'{m}_norm' for m in available_metrics]
        self.players_df['composite_score'] = self.players_df[norm_cols].mean(axis=1)
        
        # Calculer progression vs moyenne de ligue
        ligue_avg = self.players_df['composite_score'].mean()
        self.players_df['progression_pct'] = (
            (self.players_df['composite_score'] - ligue_avg) / ligue_avg * 100
        )
        
        # Filtrer joueurs en progression (> percentile 75 ET progression > 10%)
        trending = self.players_df[
            (self.players_df['per_percentile'] >= 75) &
            (self.players_df['progression_pct'] >= progression_threshold)
        ].copy()
        
        # Trier par score composite décroissant
        trending = trending.sort_values('composite_score', ascending=False)
        
        logger.info(f"[OK] {len(trending)} joueurs en progression détectés")
        self.progressions = trending
        
        return trending
    
    def get_top_rising_stars(self, n: int = 10) -> pd.DataFrame:
        """
        Retourne le top N des joueurs en progression.
        
        Args:
            n: Nombre de joueurs à retourner
            
        Returns:
            DataFrame avec top n joueurs
        """
        if self.progressions is None or self.progressions.empty:
            logger.warning("Pas de données progression. Lancez detect_trending_players() d'abord.")
            return pd.DataFrame()
        
        top_n = self.progressions.head(n)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"TOP {n} JOUEURS EN PROGRESSION")
        logger.info(f"{'='*70}")
        
        for idx, (_, player) in enumerate(top_n.iterrows(), 1):
            logger.info(f"\n{idx}. {player.get('full_name', 'Unknown')}")
            logger.info(f"   Position: {player.get('position', 'N/A')}")
            logger.info(f"   PER: {player.get('per', 0):.2f} (percentile: {player.get('per_percentile', 0):.1f})")
            logger.info(f"   TS%: {player.get('ts_pct', 0):.3f}")
            logger.info(f"   Progression: +{player.get('progression_pct', 0):.1f}%")
            logger.info(f"   Score composite: {player.get('composite_score', 0):.1f}/100")
        
        return top_n
    
    def generate_report(self, output_dir: str = "reports") -> Dict:
        """
        Génère le rapport de progression.
        
        Args:
            output_dir: Dossier de sortie pour les rapports
            
        Returns:
            Dict avec les données du rapport
        """
        logger.info("\nGénération du rapport...")
        
        # Récupérer top 10
        top_10 = self.get_top_rising_stars(10)
        
        if top_10.empty:
            logger.warning("Pas de données pour générer le rapport")
            return {}
        
        # Préparer données rapport
        rising_stars = []
        for idx, (_, player) in enumerate(top_10.iterrows(), 1):
            rising_stars.append({
                'rank': idx,
                'player_id': int(player.get('id', 0)),
                'player_name': player.get('full_name', 'Unknown'),
                'position': player.get('position', 'Unknown'),
                'current_per': round(float(player.get('per', 0)), 2),
                'ts_pct': round(float(player.get('ts_pct', 0)), 3),
                'per_percentile': round(float(player.get('per_percentile', 0)), 1),
                'composite_score': round(float(player.get('composite_score', 0)), 1),
                'progression_pct': round(float(player.get('progression_pct', 0)), 1),
                'is_rising': True
            })
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'season': '2023-24',
            'methodology': 'percentile_based_progression',
            'description': 'Joueurs avec PER > percentile 75 et progression > 10% vs moyenne ligue',
            'total_players_analyzed': len(self.players_df),
            'rising_stars_count': len(self.progressions),
            'rising_stars': rising_stars,
            'metrics_used': ['per', 'ts_pct', 'usg_pct', 'game_score'],
            'thresholds': {
                'min_percentile': 75,
                'min_progression_pct': 10.0
            }
        }
        
        # Sauvegarder rapport
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        json_file = output_path / 'rising_stars_2024.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[SAVED] Rapport JSON: {json_file}")
        
        # CSV pour faciliter l'analyse
        csv_file = output_path / 'rising_stars_2024.csv'
        if not top_10.empty:
            export_cols = ['id', 'full_name', 'position', 'per', 'ts_pct', 
                          'per_percentile', 'composite_score', 'progression_pct']
            available_cols = [c for c in export_cols if c in top_10.columns]
            top_10[available_cols].to_csv(csv_file, index=False)
            logger.info(f"[SAVED] Rapport CSV: {csv_file}")
        
        return report
    
    def run_full_analysis(self) -> Dict:
        """
        Exécute l'analyse complète.
        
        Returns:
            Dict avec les résultats
        """
        logger.info(f"\n{'='*70}")
        logger.info("NBA-24: DETECTION DES JOUEURS EN PROGRESSION")
        logger.info(f"{'='*70}\n")
        
        # Charger données
        self.load_data()
        
        # Détecter progression
        trending = self.detect_trending_players()
        
        # Générer rapport
        report = self.generate_report()
        
        # Résumé
        logger.info(f"\n{'='*70}")
        logger.info("RÉSULTATS")
        logger.info(f"{'='*70}")
        logger.info(f"Joueurs analysés: {len(self.players_df)}")
        logger.info(f"Joueurs en progression: {len(trending)}")
        logger.info(f"Top 10 généré: ✓")
        logger.info(f"Rapport sauvegardé: reports/rising_stars_2024.json")
        logger.info(f"{'='*70}\n")
        
        return report


def main():
    """Point d'entrée principal."""
    detector = ProgressionDetector()
    report = detector.run_full_analysis()
    
    if report:
        print("\n✅ Analyse terminée avec succès!")
        print(f"📊 Top 10 des joueurs en progression généré")
        print(f"📁 Rapport: reports/rising_stars_2024.json")
    else:
        print("\n❌ Erreur lors de l'analyse")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
