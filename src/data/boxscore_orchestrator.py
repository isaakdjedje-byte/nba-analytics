#!/usr/bin/env python3
"""
BoxScoreOrchestrator - Récupération professionnelle des box scores

Architecture:
- SQLite cache centralisé
- Pool de workers (3 threads max pour éviter rate limit)
- Retry avec backoff exponentiel
- Rate limiting adaptatif
- Monitoring intégré
"""

import asyncio
import json
import logging
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from nba_api.stats.endpoints import boxscoretraditionalv2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class BoxScore:
    """Structure d'un box score."""
    game_id: str
    home_team_id: int
    away_team_id: int
    home_reb: int
    away_reb: int
    home_ast: int
    away_ast: int
    home_stl: int
    away_stl: int
    home_blk: int
    away_blk: int
    home_tov: int
    away_tov: int
    home_pf: int
    away_pf: int
    home_fg_pct: float
    away_fg_pct: float
    home_fg3_pct: float
    away_fg3_pct: float
    home_ft_pct: float
    away_ft_pct: float
    fetched_at: datetime


class BoxScoreCache:
    """Cache SQLite pour les box scores."""
    
    def __init__(self, db_path: str = "data/boxscore_cache.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialise le schéma SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS boxscores (
                    game_id TEXT PRIMARY KEY,
                    home_team_id INTEGER,
                    away_team_id INTEGER,
                    home_reb INTEGER,
                    away_reb INTEGER,
                    home_ast INTEGER,
                    away_ast INTEGER,
                    home_stl INTEGER,
                    away_stl INTEGER,
                    home_blk INTEGER,
                    away_blk INTEGER,
                    home_tov INTEGER,
                    away_tov INTEGER,
                    home_pf INTEGER,
                    away_pf INTEGER,
                    home_fg_pct REAL,
                    away_fg_pct REAL,
                    home_fg3_pct REAL,
                    away_fg3_pct REAL,
                    home_ft_pct REAL,
                    away_ft_pct REAL,
                    fetched_at TIMESTAMP,
                    attempts INTEGER DEFAULT 1
                )
            """)
            
            # Index pour performances
            conn.execute("CREATE INDEX IF NOT EXISTS idx_game_id ON boxscores(game_id)")
            conn.commit()
    
    def get(self, game_id: str) -> Optional[BoxScore]:
        """Récupère un box score du cache."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM boxscores WHERE game_id = ?",
                (game_id,)
            ).fetchone()
            
            if row:
                return BoxScore(
                    game_id=row[0],
                    home_team_id=row[1],
                    away_team_id=row[2],
                    home_reb=row[3],
                    away_reb=row[4],
                    home_ast=row[5],
                    away_ast=row[6],
                    home_stl=row[7],
                    away_stl=row[8],
                    home_blk=row[9],
                    away_blk=row[10],
                    home_tov=row[11],
                    away_tov=row[12],
                    home_pf=row[13],
                    away_pf=row[14],
                    home_fg_pct=row[15],
                    away_fg_pct=row[16],
                    home_fg3_pct=row[17],
                    away_fg3_pct=row[18],
                    home_ft_pct=row[19],
                    away_ft_pct=row[20],
                    fetched_at=datetime.fromisoformat(row[21])
                )
        return None
    
    def set(self, boxscore: BoxScore):
        """Sauvegarde un box score dans le cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO boxscores 
                (game_id, home_team_id, away_team_id, home_reb, away_reb,
                 home_ast, away_ast, home_stl, away_stl, home_blk, away_blk,
                 home_tov, away_tov, home_pf, away_pf, home_fg_pct, away_fg_pct,
                 home_fg3_pct, away_fg3_pct, home_ft_pct, away_ft_pct, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                boxscore.game_id, boxscore.home_team_id, boxscore.away_team_id,
                boxscore.home_reb, boxscore.away_reb, boxscore.home_ast, boxscore.away_ast,
                boxscore.home_stl, boxscore.away_stl, boxscore.home_blk, boxscore.away_blk,
                boxscore.home_tov, boxscore.away_tov, boxscore.home_pf, boxscore.away_pf,
                boxscore.home_fg_pct, boxscore.away_fg_pct, boxscore.home_fg3_pct,
                boxscore.away_fg3_pct, boxscore.home_ft_pct, boxscore.away_ft_pct,
                boxscore.fetched_at.isoformat()
            ))
            conn.commit()
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du cache."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM boxscores").fetchone()[0]
            recent = conn.execute(
                "SELECT COUNT(*) FROM boxscores WHERE fetched_at > datetime('now', '-7 days')"
            ).fetchone()[0]
            return {'total_cached': total, 'recent': recent}


class MetricsCollector:
    """Collecte les métriques de performance."""
    
    def __init__(self):
        self.cache_hits = 0
        self.api_calls = 0
        self.errors = 0
        self.retries = 0
        self.start_time = time.time()
        
    def cache_hit(self):
        self.cache_hits += 1
        
    def api_call(self):
        self.api_calls += 1
        
    def error(self):
        self.errors += 1
        
    def retry(self):
        self.retries += 1
        
    def report(self) -> Dict:
        elapsed = time.time() - self.start_time
        return {
            'cache_hits': self.cache_hits,
            'api_calls': self.api_calls,
            'errors': self.errors,
            'retries': self.retries,
            'elapsed_seconds': elapsed,
            'avg_time_per_call': elapsed / max(self.api_calls, 1)
        }


class BoxScoreOrchestrator:
    """
    Orchestrateur professionnel pour la récupération des box scores.
    """
    
    def __init__(self, max_workers: int = 3, delay: float = 1.0):
        """
        Args:
            max_workers: Nombre de workers (3 max pour éviter rate limit)
            delay: Délai entre les requêtes (secondes)
        """
        self.cache = BoxScoreCache()
        self.max_workers = max_workers
        self.delay = delay
        self.metrics = MetricsCollector()
        
    def _fetch_single(self, game_id: str) -> Optional[BoxScore]:
        """
        Récupère un box score avec retry.
        """
        # Vérifier cache d'abord
        if cached := self.cache.get(game_id):
            self.metrics.cache_hit()
            logger.debug(f"Cache hit: {game_id}")
            return cached
        
        # Retry avec backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Rate limiting
                time.sleep(self.delay)
                
                logger.debug(f"Fetching {game_id} (attempt {attempt + 1})")
                
                # Appel API
                boxscore_data = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
                team_stats = boxscore_data.team_stats.get_data_frame()
                
                if len(team_stats) < 2:
                    logger.warning(f"Pas assez de données pour {game_id}")
                    return None
                
                # Extraire données home/away
                home_team = team_stats.iloc[0]
                away_team = team_stats.iloc[1]
                
                # Créer objet BoxScore
                boxscore = BoxScore(
                    game_id=game_id,
                    home_team_id=int(home_team['TEAM_ID']),
                    away_team_id=int(away_team['TEAM_ID']),
                    home_reb=int(home_team['REB']),
                    away_reb=int(away_team['REB']),
                    home_ast=int(home_team['AST']),
                    away_ast=int(away_team['AST']),
                    home_stl=int(home_team['STL']),
                    away_stl=int(away_team['STL']),
                    home_blk=int(home_team['BLK']),
                    away_blk=int(away_team['BLK']),
                    home_tov=int(home_team['TOV']),
                    away_tov=int(away_team['TOV']),
                    home_pf=int(home_team['PF']),
                    away_pf=int(away_team['PF']),
                    home_fg_pct=float(home_team['FG_PCT']),
                    away_fg_pct=float(away_team['FG_PCT']),
                    home_fg3_pct=float(home_team['FG3_PCT']),
                    away_fg3_pct=float(away_team['FG3_PCT']),
                    home_ft_pct=float(home_team['FT_PCT']),
                    away_ft_pct=float(away_team['FT_PCT']),
                    fetched_at=datetime.now()
                )
                
                # Sauvegarder dans cache
                self.cache.set(boxscore)
                self.metrics.api_call()
                
                logger.debug(f"✓ Fetched: {game_id}")
                return boxscore
                
            except Exception as e:
                self.metrics.error()
                wait = 2 ** attempt  # Backoff: 1, 2, 4 secondes
                logger.warning(f"Erreur {game_id} (attempt {attempt + 1}): {e}. Retry dans {wait}s...")
                time.sleep(wait)
                self.metrics.retry()
        
        logger.error(f"❌ Échec définitif pour {game_id}")
        return None
    
    def fetch_batch(self, game_ids: List[str]) -> List[Optional[BoxScore]]:
        """
        Récupère un batch de box scores en parallèle.
        """
        logger.info(f"Récupération de {len(game_ids)} box scores avec {self.max_workers} workers...")
        
        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Soumettre toutes les tâches
            future_to_game = {
                executor.submit(self._fetch_single, game_id): game_id 
                for game_id in game_ids
            }
            
            # Récupérer les résultats au fur et à mesure
            for future in as_completed(future_to_game):
                game_id = future_to_game[future]
                completed += 1
                
                if completed % 50 == 0:
                    logger.info(f"  Progression: {completed}/{len(game_ids)}")
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Exception pour {game_id}: {e}")
                    results.append(None)
        
        # Rapport
        successful = len([r for r in results if r is not None])
        logger.info(f"✓ Terminé: {successful}/{len(game_ids)} récupérés")
        
        metrics = self.metrics.report()
        logger.info(f"  Cache hits: {metrics['cache_hits']}")
        logger.info(f"  API calls: {metrics['api_calls']}")
        logger.info(f"  Erreurs: {metrics['errors']}")
        logger.info(f"  Retries: {metrics['retries']}")
        logger.info(f"  Temps: {metrics['elapsed_seconds']:.1f}s")
        
        return results


def main():
    """Test du module."""
    print("\n" + "="*70)
    print("TEST BOXSCORE ORCHESTRATOR")
    print("="*70 + "\n")
    
    # Test avec quelques matchs
    test_games = ['0022500001', '0022500002', '0022500003']
    
    orchestrator = BoxScoreOrchestrator(max_workers=2, delay=1.0)
    results = orchestrator.fetch_batch(test_games)
    
    print("\nRésultats:")
    for game_id, result in zip(test_games, results):
        if result:
            print(f"  {game_id}: ✓ (Home Reb: {result.home_reb}, Away Reb: {result.away_reb})")
        else:
            print(f"  {game_id}: ✗ Échec")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
