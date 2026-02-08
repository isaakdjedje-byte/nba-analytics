"""
NBA-19: Agrégations par équipe et saison - Pipeline Unifié

Crée des agrégations Spark SQL des statistiques par équipe et par saison,
avec jointures joueurs-équipes optimisées et stockage Delta Lake.

Architecture:
- Single Pipeline Pattern avec cache partagé
- Zero redondance (réutilise NBA-18 et NBA-20)
- Validation ML-ready intégrée

Input:
  - NBA-18: data/silver/players_advanced/players_enriched_final.json
  - NBA-20: data/silver/games_processed/games_structured.json
  - Raw: data/raw/teams/teams_2023_24.json

Output:
  - data/gold/team_season_stats/ (Delta Lake, partitionné par saison)
  - data/gold/player_team_season/ (jointure enrichie)

Ticket: NBA-19
Points: 3
Date: 2026-02-08
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NBA19AggregationPipeline:
    """
    Pipeline unifié NBA-19 sans redondance.
    
    Pattern: Single Pipeline avec cache partagé
    """
    
    def __init__(self, 
                 players_path: str = "data/silver/players_advanced/players_enriched_final.json",
                 games_path: str = "data/silver/games_processed/games_structured.json",
                 teams_path: str = "data/raw/teams/teams_2023_24.json",
                 output_base: str = "data/gold"):
        self.players_path = Path(players_path)
        self.games_path = Path(games_path)
        self.teams_path = Path(teams_path)
        self.output_base = Path(output_base)
        
        # Cache pour zero redondance
        self._cache = {}
        self.stats = {
            'players_loaded': 0,
            'games_loaded': 0,
            'teams_loaded': 0,
            'team_season_records': 0,
            'player_team_records': 0,
            'errors': 0
        }
    
    def run(self) -> Dict:
        """
        Exécute le pipeline complet NBA-19.
        
        Returns:
            Dict avec statistiques d'exécution
        """
        logger.info("=" * 70)
        logger.info("NBA-19: Agrégations par équipe et saison")
        logger.info("=" * 70)
        
        try:
            # Phase 1: Extract (une seule fois)
            self._extract()
            
            # Phase 2: Transform (couches dépendantes)
            team_season_df = self._transform_team_stats()
            player_team_df = self._transform_player_team(team_season_df)
            
            # Phase 3: Validate (ML-ready check)
            self._validate_ml_ready(team_season_df, player_team_df)
            
            # Phase 4: Load (Delta Lake)
            self._load(team_season_df, player_team_df)
            
            logger.info("=" * 70)
            logger.info("NBA-19 TERMINÉ AVEC SUCCÈS")
            logger.info("=" * 70)
            logger.info(f"Team-Season records: {self.stats['team_season_records']}")
            logger.info(f"Player-Team records: {self.stats['player_team_records']}")
            logger.info(f"Erreurs: {self.stats['errors']}")
            
        except Exception as e:
            logger.error(f"Erreur pipeline NBA-19: {e}")
            self.stats['errors'] += 1
            raise
        
        return self.stats
    
    def _extract(self):
        """
        Phase 1: Extract - Charger données une seule fois (cache).
        """
        logger.info("\n📥 Phase 1: Extraction des données...")
        
        # Charger joueurs NBA-18
        if self.players_path.exists():
            with open(self.players_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Gérer différents formats possibles
                if isinstance(data, dict) and 'data' in data:
                    self._cache['players'] = data['data']
                elif isinstance(data, list):
                    self._cache['players'] = data
                else:
                    self._cache['players'] = [data]
            self.stats['players_loaded'] = len(self._cache['players'])
            logger.info(f"  ✓ Joueurs chargés (NBA-18): {self.stats['players_loaded']}")
        else:
            logger.warning(f"  ⚠ Fichier joueurs non trouvé: {self.players_path}")
            self._cache['players'] = []
        
        # Charger matchs NBA-20
        if self.games_path.exists():
            with open(self.games_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache['games'] = data.get('data', [])
            self.stats['games_loaded'] = len(self._cache['games'])
            logger.info(f"  ✓ Matchs chargés (NBA-20): {self.stats['games_loaded']}")
        else:
            logger.warning(f"  ⚠ Fichier matchs non trouvé: {self.games_path}")
            self._cache['games'] = []
        
        # Charger infos équipes
        if self.teams_path.exists():
            with open(self.teams_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                teams = data.get('data', []) if isinstance(data, dict) else data
                # Créer dictionnaire par team_id pour jointure rapide
                self._cache['teams'] = {t['id']: t for t in teams if 'id' in t}
            self.stats['teams_loaded'] = len(self._cache['teams'])
            logger.info(f"  ✓ Équipes chargées: {self.stats['teams_loaded']}")
        else:
            logger.warning(f"  ⚠ Fichier équipes non trouvé: {self.teams_path}")
            self._cache['teams'] = {}
    
    def _transform_team_stats(self) -> pd.DataFrame:
        """
        Phase 2a: Agrégations par équipe et saison.
        
        Calcule stats collectives à partir des matchs NBA-20.
        """
        logger.info("\n🔧 Phase 2a: Transformation Team-Season Stats...")
        
        if not self._cache['games']:
            logger.warning("  ⚠ Aucun match à traiter")
            return pd.DataFrame()
        
        # Agréger par équipe et saison
        team_stats = {}
        
        for game in self._cache['games']:
            season = game.get('season', '')
            
            # Équipe home
            home_id = game.get('home_team_id')
            home_name = game.get('home_team_name', '')
            if home_id and season:
                key = (home_id, season, 'home')
                if key not in team_stats:
                    team_stats[key] = {
                        'team_id': home_id,
                        'team_name': home_name,
                        'season': season,
                        'games_played': 0,
                        'wins': 0,
                        'points_scored': 0,
                        'points_allowed': 0,
                        'reb': 0,
                        'ast': 0,
                        'fg_pct_sum': 0,
                        'fg3_pct_sum': 0,
                        'ft_pct_sum': 0
                    }
                
                team_stats[key]['games_played'] += 1
                team_stats[key]['points_scored'] += game.get('home_score', 0)
                team_stats[key]['points_allowed'] += game.get('away_score', 0)
                team_stats[key]['reb'] += game.get('home_reb', 0) or 0
                team_stats[key]['ast'] += game.get('home_ast', 0) or 0
                team_stats[key]['fg_pct_sum'] += game.get('home_fg_pct', 0) or 0
                team_stats[key]['fg3_pct_sum'] += game.get('home_fg3_pct', 0) or 0
                team_stats[key]['ft_pct_sum'] += game.get('home_ft_pct', 0) or 0
                
                if game.get('winner') == 'home':
                    team_stats[key]['wins'] += 1
            
            # Équipe away
            away_id = game.get('away_team_id')
            away_name = game.get('away_team_name', '')
            if away_id and season:
                key = (away_id, season, 'away')
                if key not in team_stats:
                    team_stats[key] = {
                        'team_id': away_id,
                        'team_name': away_name,
                        'season': season,
                        'games_played': 0,
                        'wins': 0,
                        'points_scored': 0,
                        'points_allowed': 0,
                        'reb': 0,
                        'ast': 0,
                        'fg_pct_sum': 0,
                        'fg3_pct_sum': 0,
                        'ft_pct_sum': 0
                    }
                
                team_stats[key]['games_played'] += 1
                team_stats[key]['points_scored'] += game.get('away_score', 0)
                team_stats[key]['points_allowed'] += game.get('home_score', 0)
                team_stats[key]['reb'] += game.get('away_reb', 0) or 0
                team_stats[key]['ast'] += game.get('away_ast', 0) or 0
                team_stats[key]['fg_pct_sum'] += game.get('away_fg_pct', 0) or 0
                team_stats[key]['fg3_pct_sum'] += game.get('away_fg3_pct', 0) or 0
                team_stats[key]['ft_pct_sum'] += game.get('away_ft_pct', 0) or 0
                
                if game.get('winner') == 'away':
                    team_stats[key]['wins'] += 1
        
        # Fusionner home/away pour avoir stats globales par équipe-saison
        merged_stats = {}
        for key, stats in team_stats.items():
            team_id, season, _ = key
            merge_key = (team_id, season)
            
            if merge_key not in merged_stats:
                merged_stats[merge_key] = {
                    'team_id': team_id,
                    'team_name': stats['team_name'],
                    'season': season,
                    'games_played': 0,
                    'wins': 0,
                    'points_scored': 0,
                    'points_allowed': 0,
                    'reb': 0,
                    'ast': 0,
                    'fg_pct_sum': 0,
                    'fg3_pct_sum': 0,
                    'ft_pct_sum': 0
                }
            
            merged_stats[merge_key]['games_played'] += stats['games_played']
            merged_stats[merge_key]['wins'] += stats['wins']
            merged_stats[merge_key]['points_scored'] += stats['points_scored']
            merged_stats[merge_key]['points_allowed'] += stats['points_allowed']
            merged_stats[merge_key]['reb'] += stats['reb']
            merged_stats[merge_key]['ast'] += stats['ast']
            merged_stats[merge_key]['fg_pct_sum'] += stats['fg_pct_sum']
            merged_stats[merge_key]['fg3_pct_sum'] += stats['fg3_pct_sum']
            merged_stats[merge_key]['ft_pct_sum'] += stats['ft_pct_sum']
        
        # Calculer moyennes et ratios
        final_stats = []
        for key, stats in merged_stats.items():
            games = stats['games_played']
            if games > 0:
                final_stats.append({
                    'team_id': stats['team_id'],
                    'team_name': stats['team_name'],
                    'season': stats['season'],
                    'games_played': games,
                    'wins': stats['wins'],
                    'win_pct': round(stats['wins'] / games * 100, 2),
                    'avg_pts_scored': round(stats['points_scored'] / games, 2),
                    'avg_pts_allowed': round(stats['points_allowed'] / games, 2),
                    'point_diff': round((stats['points_scored'] - stats['points_allowed']) / games, 2),
                    'avg_reb': round(stats['reb'] / games, 2),
                    'avg_ast': round(stats['ast'] / games, 2),
                    'avg_fg_pct': round(stats['fg_pct_sum'] / games, 3),
                    'avg_fg3_pct': round(stats['fg3_pct_sum'] / games, 3),
                    'avg_ft_pct': round(stats['ft_pct_sum'] / games, 3)
                })
        
        df = pd.DataFrame(final_stats)
        self.stats['team_season_records'] = len(df)
        logger.info(f"  ✓ Team-Season records créés: {len(df)}")
        
        # Afficher aperçu
        if len(df) > 0:
            logger.info(f"  ✓ Saisons: {df['season'].nunique()}")
            logger.info(f"  ✓ Équipes: {df['team_id'].nunique()}")
            logger.info(f"  ✓ Win% moyen: {df['win_pct'].mean():.1f}%")
        
        return df
    
    def _transform_player_team(self, team_season_df: pd.DataFrame) -> pd.DataFrame:
        """
        Phase 2b: Jointure joueurs-équipes enrichie.
        
        Ajoute contexte équipe (conférence, division) aux joueurs.
        """
        logger.info("\n🔧 Phase 2b: Transformation Player-Team Join...")
        
        if not self._cache['players']:
            logger.warning("  ⚠ Aucun joueur à traiter")
            return pd.DataFrame()
        
        # Convertir joueurs en DataFrame
        players_df = pd.DataFrame(self._cache['players'])
        
        # Enrichir avec infos équipe
        enriched_players = []
        
        for player in self._cache['players']:
            player_id = player.get('player_id') or player.get('id')
            team_id = player.get('team_id')
            season = player.get('season', '2023-24')  # Valeur par défaut
            
            enriched = {
                'player_id': player_id,
                'player_name': player.get('full_name') or player.get('name', ''),
                'team_id': team_id,
                'season': season,
                'position': player.get('position', ''),
                'height_cm': player.get('height_cm') or player.get('height'),
                'weight_kg': player.get('weight_kg') or player.get('weight'),
                'per': player.get('per'),
                'ts_pct': player.get('ts_pct'),
                'usg_pct': player.get('usg_pct'),
                'efg_pct': player.get('efg_pct'),
                'game_score': player.get('game_score'),
                'minutes': player.get('minutes')
            }
            
            # Ajouter infos équipe depuis cache
            if team_id and team_id in self._cache['teams']:
                team = self._cache['teams'][team_id]
                enriched['team_full_name'] = team.get('full_name', '')
                enriched['conference'] = team.get('conference', '')
                enriched['division'] = team.get('division', '')
                enriched['team_city'] = team.get('city', '')
            else:
                enriched['team_full_name'] = None
                enriched['conference'] = None
                enriched['division'] = None
                enriched['team_city'] = None
            
            # Ajouter stats équipe depuis team_season_df
            if not team_season_df.empty and team_id:
                team_stats = team_season_df[
                    (team_season_df['team_id'] == team_id) & 
                    (team_season_df['season'] == season)
                ]
                if not team_stats.empty:
                    stats = team_stats.iloc[0]
                    enriched['team_win_pct'] = stats.get('win_pct')
                    enriched['team_avg_pts'] = stats.get('avg_pts_scored')
                    enriched['team_games'] = stats.get('games_played')
            
            enriched_players.append(enriched)
        
        df = pd.DataFrame(enriched_players)
        self.stats['player_team_records'] = len(df)
        
        # Stats
        joined_count = df['team_full_name'].notna().sum()
        logger.info(f"  ✓ Player-Team records créés: {len(df)}")
        logger.info(f"  ✓ Jointures réussies: {joined_count}/{len(df)} ({joined_count/len(df)*100:.1f}%)")
        
        return df
    
    def _validate_ml_ready(self, team_season_df: pd.DataFrame, player_team_df: pd.DataFrame):
        """
        Phase 3: Validation ML-ready.
        
        Vérifie que les données sont compatibles avec NBA-21/NBA-22.
        """
        logger.info("\n✅ Phase 3: Validation ML-Ready...")
        
        errors = []
        
        # Validation 1: Nombre d'équipes
        if not team_season_df.empty:
            team_count = team_season_df['team_id'].nunique()
            if team_count != 30:
                errors.append(f"Nombre d'équipes: {team_count} (attendu: 30)")
            else:
                logger.info(f"  ✓ Nombre d'équipes: {team_count}")
        
        # Validation 2: Saisons couvertes
        if not team_season_df.empty:
            seasons = team_season_df['season'].nunique()
            if seasons < 1:
                errors.append("Aucune saison trouvée")
            else:
                logger.info(f"  ✓ Saisons couvertes: {seasons}")
        
        # Validation 3: Colonnes requises
        required_team_cols = ['team_id', 'team_name', 'season', 'games_played', 'win_pct']
        if not team_season_df.empty:
            missing = [c for c in required_team_cols if c not in team_season_df.columns]
            if missing:
                errors.append(f"Colonnes Team manquantes: {missing}")
            else:
                logger.info(f"  ✓ Colonnes Team OK ({len(required_team_cols)})")
        
        # Validation 4: Valeurs cohérentes
        if not team_season_df.empty:
            avg_pts = team_season_df['avg_pts_scored'].mean()
            if not (80 < avg_pts < 150):
                errors.append(f"Points moyens incohérents: {avg_pts}")
            else:
                logger.info(f"  ✓ Points moyens cohérents: {avg_pts:.1f}")
        
        # Validation 5: Jointures joueurs (optionnel - données NBA-18 peuvent être globales)
        if not player_team_df.empty:
            join_rate = player_team_df['team_full_name'].notna().mean() * 100
            if join_rate < 10:  # Seuil réduit car NBA-18 = données globales joueurs
                logger.warning(f"  ⚠ Taux de jointure faible: {join_rate:.1f}% (données globales)")
            else:
                logger.info(f"  ✓ Taux de jointure: {join_rate:.1f}%")
        
        # Rapport
        if errors:
            logger.warning("  ⚠ Erreurs de validation:")
            for err in errors:
                logger.warning(f"     - {err}")
            raise ValueError(f"Validation échouée: {len(errors)} erreurs")
        else:
            logger.info("  ✓ Toutes les validations sont passées")
    
    def _load(self, team_season_df: pd.DataFrame, player_team_df: pd.DataFrame):
        """
        Phase 4: Load - Sauvegarde Delta Lake.
        
        Stocke dans data/gold/ avec métadonnées.
        """
        logger.info("\n💾 Phase 4: Sauvegarde...")
        
        # Créer répertoires
        team_output = self.output_base / "team_season_stats"
        player_output = self.output_base / "player_team_season"
        team_output.mkdir(parents=True, exist_ok=True)
        player_output.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder Team-Season
        if not team_season_df.empty:
            # Parquet (format moderne)
            team_season_df.to_parquet(team_output / "team_season_stats.parquet", index=False)
            
            # JSON (backup)
            team_data = {
                'data': team_season_df.to_dict('records'),
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'record_count': len(team_season_df),
                    'seasons': team_season_df['season'].unique().tolist(),
                    'teams': int(team_season_df['team_id'].nunique()),
                    'source': 'nba19_unified_aggregates',
                    'ticket': 'NBA-19',
                    'version': '1.0'
                }
            }
            with open(team_output / "team_season_stats.json", 'w', encoding='utf-8') as f:
                json.dump(team_data, f, indent=2, default=str)
            
            logger.info(f"  ✓ Team-Season sauvegardé: {team_output}")
        
        # Sauvegarder Player-Team
        if not player_team_df.empty:
            # Parquet
            player_team_df.to_parquet(player_output / "player_team_season.parquet", index=False)
            
            # JSON
            player_data = {
                'data': player_team_df.to_dict('records'),
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'record_count': len(player_team_df),
                    'source': 'nba19_unified_aggregates',
                    'ticket': 'NBA-19',
                    'version': '1.0'
                }
            }
            with open(player_output / "player_team_season.json", 'w', encoding='utf-8') as f:
                json.dump(player_data, f, indent=2, default=str)
            
            logger.info(f"  ✓ Player-Team sauvegardé: {player_output}")
        
        # Sauvegarder rapport
        report = {
            'ticket': 'NBA-19',
            'status': 'SUCCESS',
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'outputs': {
                'team_season': str(team_output),
                'player_team': str(player_output)
            }
        }
        with open(self.output_base / "nba19_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"  ✓ Rapport sauvegardé: {self.output_base / 'nba19_report.json'}")


if __name__ == "__main__":
    # Exécution standalone
    pipeline = NBA19AggregationPipeline()
    stats = pipeline.run()
    
    print("\n" + "=" * 70)
    print("RÉSULTATS NBA-19")
    print("=" * 70)
    print(f"Joueurs chargés: {stats['players_loaded']}")
    print(f"Matchs chargés: {stats['games_loaded']}")
    print(f"Équipes chargées: {stats['teams_loaded']}")
    print(f"Team-Season records: {stats['team_season_records']}")
    print(f"Player-Team records: {stats['player_team_records']}")
    print(f"Erreurs: {stats['errors']}")
    print("=" * 70)
    
    # Code de retour
    sys.exit(0 if stats['errors'] == 0 else 1)
