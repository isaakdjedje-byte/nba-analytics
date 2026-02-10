#!/usr/bin/env python3
"""
BoxScoreOrchestrator V2 - Avec PlayerGameLogs pour contrôle maximal

Cette version utilise PlayerGameLogs au lieu de BoxScoreTraditionalV2,
permettant un contrôle total sur l'agrégation des stats et la validation.
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelogs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TeamBoxScore:
    """Box score agrégé au niveau équipe avec validation."""
    game_id: str
    team_id: int
    team_name: str
    is_home: bool
    
    # Stats de base
    pts: int
    reb: int
    ast: int
    stl: int
    blk: int
    tov: int
    pf: int
    
    # Shooting
    fgm: int
    fga: int
    fg_pct: float
    fg3m: int
    fg3a: int
    fg3_pct: float
    ftm: int
    fta: int
    ft_pct: float
    
    # Métadonnées
    players_count: int  # Nombre de joueurs agrégés
    total_minutes: float  # Minutes totales d'équipe
    validation_score: float  # Score de validation (0-1)
    fetched_at: datetime


class BoxScoreOrchestratorV2:
    """
    Orchestrateur utilisant PlayerGameLogs pour un contrôle maximal.
    """
    
    def __init__(self, 
                 min_minutes: float = 5.0,  # Joueurs avec < 5 min ignorés
                 validation_threshold: float = 0.95,  # Seuil validation
                 cache_db: str = "data/boxscore_cache_v2.db"):
        self.min_minutes = min_minutes
        self.validation_threshold = validation_threshold
        self.cache_db = Path(cache_db)
        self.cache_db.parent.mkdir(parents=True, exist_ok=True)
        self._init_cache()
        
    def _init_cache(self):
        """Initialise le cache SQLite."""
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS boxscores (
                    game_id TEXT,
                    team_id INTEGER,
                    team_name TEXT,
                    is_home BOOLEAN,
                    pts INTEGER,
                    reb INTEGER,
                    ast INTEGER,
                    stl INTEGER,
                    blk INTEGER,
                    tov INTEGER,
                    pf INTEGER,
                    fgm INTEGER,
                    fga INTEGER,
                    fg_pct REAL,
                    fg3m INTEGER,
                    fg3a INTEGER,
                    fg3_pct REAL,
                    ftm INTEGER,
                    fta INTEGER,
                    ft_pct REAL,
                    players_count INTEGER,
                    total_minutes REAL,
                    validation_score REAL,
                    fetched_at TIMESTAMP,
                    PRIMARY KEY (game_id, team_id)
                )
            """)
            conn.commit()
    
    def _fetch_player_logs(self, season: str = '2025-26') -> Optional[pd.DataFrame]:
        """
        Récupère tous les logs joueurs pour une saison.
        """
        try:
            logger.info(f"Récupération PlayerGameLogs pour {season}...")
            
            logs = playergamelogs.PlayerGameLogs(
                season_nullable=season,
                season_type_nullable='Regular Season'
            )
            
            df = logs.get_data_frames()[0]
            logger.info(f"✓ {len(df)} logs joueurs récupérés")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération logs: {e}")
            return None
    
    def _filter_players(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtre les joueurs selon critères de qualité.
        """
        initial_count = len(df)
        
        # 1. Filtrer joueurs avec très peu de minutes
        df_filtered = df[df['MIN'] >= self.min_minutes].copy()
        logger.info(f"  Filtrage minutes >= {self.min_minutes}: {initial_count} → {len(df_filtered)}")
        
        # 2. Filtrer joueurs sans stats significatives (0 PTS, 0 REB, 0 AST)
        mask_stats = (df_filtered['PTS'] > 0) | (df_filtered['REB'] > 0) | (df_filtered['AST'] > 0)
        df_filtered = df_filtered[mask_stats].copy()
        logger.info(f"  Filtrage stats > 0: → {len(df_filtered)}")
        
        # 3. Calculer efficacité (points par minute)
        df_filtered['EFFICIENCY'] = df_filtered['PTS'] / df_filtered['MIN'].clip(lower=1)
        
        return df_filtered
    
    def _aggregate_to_team(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrège les stats joueurs au niveau équipe avec pondération.
        """
        logger.info("Agrégation au niveau équipe...")
        
        # Déterminer si équipe à domicile depuis MATCHUP
        df['IS_HOME'] = df['MATCHUP'].str.contains('vs.')
        
        # Agrégation
        agg_dict = {
            'PTS': 'sum',
            'REB': 'sum',
            'AST': 'sum',
            'STL': 'sum',
            'BLK': 'sum',
            'TOV': 'sum',
            'PF': 'sum',
            'FGM': 'sum',
            'FGA': 'sum',
            'FG3M': 'sum',
            'FG3A': 'sum',
            'FTM': 'sum',
            'FTA': 'sum',
            'MIN': 'sum',
            'PLAYER_ID': 'count',  # Nombre de joueurs
            'TEAM_NAME': 'first',
            'IS_HOME': 'first',
            'GAME_DATE': 'first'
        }
        
        team_stats = df.groupby(['GAME_ID', 'TEAM_ID']).agg(agg_dict).reset_index()
        team_stats.rename(columns={'PLAYER_ID': 'PLAYERS_COUNT'}, inplace=True)
        
        # Calculer pourcentages
        team_stats['FG_PCT'] = (team_stats['FGM'] / team_stats['FGA'].clip(lower=1)).round(3)
        team_stats['FG3_PCT'] = (team_stats['FG3M'] / team_stats['FG3A'].clip(lower=1)).round(3)
        team_stats['FT_PCT'] = (team_stats['FTM'] / team_stats['FTA'].clip(lower=1)).round(3)
        
        logger.info(f"✓ {len(team_stats)} box scores équipe créés")
        return team_stats
    
    def _validate_boxscores(self, team_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Valide les box scores et calcule un score de confiance.
        """
        logger.info("Validation des box scores...")
        
        # 1. Vérifier cohérence temps de jeu (48 min régulation, 53+ OT)
        team_stats['MIN_EXPECTED'] = np.where(team_stats['MIN'] > 240, 300, 240)  # OT si > 240
        team_stats['MIN_RATIO'] = team_stats['MIN'] / team_stats['MIN_EXPECTED']
        
        # 2. Vérifier nombre de joueurs raisonnable (8-13 joueurs par équipe)
        team_stats['PLAYERS_VALID'] = (
            (team_stats['PLAYERS_COUNT'] >= 8) & 
            (team_stats['PLAYERS_COUNT'] <= 13)
        ).astype(int)
        
        # 3. Vérifier stats cohérentes (pas de valeurs négatives ou extrêmes)
        team_stats['STATS_VALID'] = (
            (team_stats['PTS'] >= 60) & (team_stats['PTS'] <= 180) &  # Scores raisonnables
            (team_stats['REB'] >= 20) & (team_stats['REB'] <= 80) &
            (team_stats['AST'] >= 10) & (team_stats['AST'] <= 50)
        ).astype(int)
        
        # 4. Calculer score de validation global
        team_stats['VALIDATION_SCORE'] = (
            team_stats['MIN_RATIO'].clip(0.8, 1.0) * 0.4 +  # 40% temps de jeu
            team_stats['PLAYERS_VALID'] * 0.3 +              # 30% nombre joueurs
            team_stats['STATS_VALID'] * 0.3                  # 30% cohérence stats
        ).round(3)
        
        # Filtrer selon seuil
        valid_mask = team_stats['VALIDATION_SCORE'] >= self.validation_threshold
        valid_count = valid_mask.sum()
        
        logger.info(f"✓ {valid_count}/{len(team_stats)} box scores valides (seuil: {self.validation_threshold})")
        
        if valid_count < len(team_stats):
            invalid = team_stats[~valid_mask]
            logger.warning(f"⚠️ {len(invalid)} box scores invalides:")
            for _, row in invalid.head(5).iterrows():
                logger.warning(f"   {row['GAME_ID']}: score={row['VALIDATION_SCORE']:.2f}")
        
        return team_stats[valid_mask].copy()
    
    def _convert_to_dataclass(self, row: pd.Series) -> TeamBoxScore:
        """Convertit une ligne DataFrame en dataclass."""
        return TeamBoxScore(
            game_id=row['GAME_ID'],
            team_id=row['TEAM_ID'],
            team_name=row['TEAM_NAME'],
            is_home=row['IS_HOME'],
            pts=int(row['PTS']),
            reb=int(row['REB']),
            ast=int(row['AST']),
            stl=int(row['STL']),
            blk=int(row['BLK']),
            tov=int(row['TOV']),
            pf=int(row['PF']),
            fgm=int(row['FGM']),
            fga=int(row['FGA']),
            fg_pct=float(row['FG_PCT']),
            fg3m=int(row['FG3M']),
            fg3a=int(row['FG3A']),
            fg3_pct=float(row['FG3_PCT']),
            ftm=int(row['FTM']),
            fta=int(row['FTA']),
            ft_pct=float(row['FT_PCT']),
            players_count=int(row['PLAYERS_COUNT']),
            total_minutes=float(row['MIN']),
            validation_score=float(row['VALIDATION_SCORE']),
            fetched_at=datetime.now()
        )
    
    def _save_to_cache(self, boxscore: TeamBoxScore):
        """Sauvegarde dans le cache SQLite."""
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO boxscores 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                boxscore.game_id, boxscore.team_id, boxscore.team_name, boxscore.is_home,
                boxscore.pts, boxscore.reb, boxscore.ast, boxscore.stl, boxscore.blk,
                boxscore.tov, boxscore.pf, boxscore.fgm, boxscore.fga, boxscore.fg_pct,
                boxscore.fg3m, boxscore.fg3a, boxscore.fg3_pct, boxscore.ftm, boxscore.fta,
                boxscore.ft_pct, boxscore.players_count, boxscore.total_minutes,
                boxscore.validation_score, boxscore.fetched_at.isoformat()
            ))
            conn.commit()
    
    def fetch_season_boxscores(self, season: str = '2025-26') -> List[TeamBoxScore]:
        """
        Récupère et valide tous les box scores pour une saison.
        
        Returns:
            Liste de TeamBoxScore validés
        """
        logger.info("="*70)
        logger.info(f"FETCH BOX SCORES {season} - VERSION CONTRÔLE MAX")
        logger.info("="*70)
        
        # 1. Récupérer logs joueurs
        df_players = self._fetch_player_logs(season)
        if df_players is None or len(df_players) == 0:
            logger.error("❌ Aucune donnée récupérée")
            return []
        
        # 2. Filtrer joueurs
        df_filtered = self._filter_players(df_players)
        
        # 3. Agréger par équipe
        team_stats = self._aggregate_to_team(df_filtered)
        
        # 4. Valider
        team_stats_valid = self._validate_boxscores(team_stats)
        
        # 5. Convertir en dataclass et sauvegarder
        boxscores = []
        for _, row in team_stats_valid.iterrows():
            boxscore = self._convert_to_dataclass(row)
            self._save_to_cache(boxscore)
            boxscores.append(boxscore)
        
        # Rapport final
        logger.info("\n" + "="*70)
        logger.info("RÉSULTATS")
        logger.info("="*70)
        logger.info(f"✓ Joueurs traités: {len(df_players)}")
        logger.info(f"✓ Joueurs filtrés: {len(df_filtered)}")
        logger.info(f"✓ Box scores créés: {len(team_stats)}")
        logger.info(f"✓ Box scores validés: {len(boxscores)}")
        logger.info(f"✓ Taux de validation: {len(boxscores)/len(team_stats)*100:.1f}%")
        
        # Stats globales
        if len(boxscores) > 0:
            avg_validation = np.mean([b.validation_score for b in boxscores])
            logger.info(f"✓ Score de validation moyen: {avg_validation:.3f}")
        
        logger.info("="*70)
        
        return boxscores
    
    def get_boxscores_for_game(self, game_id: str) -> Tuple[Optional[TeamBoxScore], Optional[TeamBoxScore]]:
        """
        Récupère les deux box scores (home et away) pour un match.
        """
        with sqlite3.connect(self.cache_db) as conn:
            rows = conn.execute(
                "SELECT * FROM boxscores WHERE game_id = ?",
                (game_id,)
            ).fetchall()
        
        if len(rows) < 2:
            return None, None
        
        boxscores = []
        for row in rows:
            boxscores.append(TeamBoxScore(
                game_id=row[0], team_id=row[1], team_name=row[2], is_home=row[3],
                pts=row[4], reb=row[5], ast=row[6], stl=row[7], blk=row[8],
                tov=row[9], pf=row[10], fgm=row[11], fga=row[12], fg_pct=row[13],
                fg3m=row[14], fg3a=row[15], fg3_pct=row[16], ftm=row[17], fta=row[18],
                ft_pct=row[19], players_count=row[20], total_minutes=row[21],
                validation_score=row[22], fetched_at=datetime.fromisoformat(row[23])
            ))
        
        home = next((b for b in boxscores if b.is_home), None)
        away = next((b for b in boxscores if not b.is_home), None)
        
        return home, away


def main():
    """Test du module."""
    print("\n" + "="*70)
    print("TEST BOXSCORE ORCHESTRATOR V2")
    print("="*70 + "\n")
    
    orchestrator = BoxScoreOrchestratorV2(
        min_minutes=5.0,
        validation_threshold=0.90
    )
    
    # Test sur 2025-26
    boxscores = orchestrator.fetch_season_boxscores('2025-26')
    
    if len(boxscores) > 0:
        print("\n✅ SUCCÈS!")
        print(f"   {len(boxscores)} box scores récupérés et validés")
        
        # Exemple
        sample = boxscores[0]
        print(f"\nExemple: {sample.team_name} (Game {sample.game_id})")
        print(f"   PTS: {sample.pts}, REB: {sample.reb}, AST: {sample.ast}")
        print(f"   Validation: {sample.validation_score:.3f}")
        print(f"   Joueurs: {sample.players_count}")
    else:
        print("\n❌ ÉCHEC - Aucun box score récupéré")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
