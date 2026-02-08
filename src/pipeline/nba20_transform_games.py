"""
NBA-20: Transformation des données matchs

Transforme les box scores bruts (2 entrées par match: home + away)
en matchs structurés pour ML (1 entrée par match).

Input: data/raw/games_boxscores/*.json (format brut API)
Output: data/silver/games_processed/ (format structuré ML)
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GamesTransformer:
    """
    Transforme les box scores NBA en matchs structurés pour ML.
    
    Format input: 2 records par match (une équipe = une ligne)
    Format output: 1 record par match avec home/away identifiés
    
    Attributes:
        input_path: Chemin vers les box scores bruts
        output_path: Chemin de sortie pour les matchs structurés
    """
    
    def __init__(self, input_path: str = "data/raw/games_boxscores", 
                 output_path: str = "data/silver/games_processed"):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.stats = {
            'total_files': 0,
            'total_records': 0,
            'unique_games': 0,
            'home_wins': 0,
            'away_wins': 0,
            'errors': 0
        }
    
    def transform_all(self) -> Dict:
        """
        Transforme tous les fichiers box scores en matchs structurés.
        
        Returns:
            Dict avec les statistiques de transformation
        """
        logger.info("=" * 60)
        logger.info("NBA-20: Transformation des données matchs")
        logger.info("=" * 60)
        
        # Charger tous les box scores
        all_records = self._load_all_boxscores()
        
        # Grouper par game_id
        games = self._group_by_game(all_records)
        
        # Transformer chaque match
        structured_games = []
        for game_id, records in games.items():
            try:
                game = self._transform_game(game_id, records)
                if game:
                    structured_games.append(game)
            except Exception as e:
                logger.error(f"Erreur transformation match {game_id}: {e}")
                self.stats['errors'] += 1
        
        # Sauvegarder
        self._save_games(structured_games)
        
        # Calculer statistiques
        self._calculate_stats(structured_games)
        
        logger.info("=" * 60)
        logger.info("Transformation terminée!")
        logger.info(f"Matchs traités: {self.stats['unique_games']}")
        logger.info(f"Home wins: {self.stats['home_wins']}")
        logger.info(f"Away wins: {self.stats['away_wins']}")
        logger.info(f"Erreurs: {self.stats['errors']}")
        logger.info("=" * 60)
        
        return self.stats
    
    def _load_all_boxscores(self) -> List[Dict]:
        """Charge tous les fichiers box scores."""
        all_records = []
        
        json_files = list(self.input_path.glob("*_games.json"))
        self.stats['total_files'] = len(json_files)
        
        logger.info(f"Chargement de {len(json_files)} fichiers box scores...")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = data.get('data', [])
                    all_records.extend(records)
                    logger.debug(f"Chargé {len(records)} records depuis {file_path.name}")
            except Exception as e:
                logger.error(f"Erreur chargement {file_path}: {e}")
        
        self.stats['total_records'] = len(all_records)
        logger.info(f"Total records chargés: {len(all_records)}")
        
        return all_records
    
    def _group_by_game(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """Groupe les records par game_id."""
        games = defaultdict(list)
        
        for record in records:
            game_id = record.get('game_id')
            if game_id:
                games[game_id].append(record)
        
        self.stats['unique_games'] = len(games)
        logger.info(f"Matchs uniques identifiés: {len(games)}")
        
        return games
    
    def _transform_game(self, game_id: str, records: List[Dict]) -> Optional[Dict]:
        """
        Transforme 2 records (home + away) en 1 match structuré.
        
        Args:
            game_id: ID du match
            records: Liste des records (doit contenir 2 équipes)
            
        Returns:
            Dict avec le match structuré ou None si invalide
        """
        if len(records) != 2:
            logger.warning(f"Match {game_id}: nombre d'équipes invalide ({len(records)})")
            return None
        
        # Identifier home et away via le champ matchup
        home_record = None
        away_record = None
        
        for record in records:
            matchup = record.get('matchup', '')
            if 'vs.' in matchup:
                home_record = record
            elif '@' in matchup:
                away_record = record
        
        if not home_record or not away_record:
            logger.warning(f"Match {game_id}: impossible d'identifier home/away")
            return None
        
        # Calculer le gagnant
        home_score = home_record.get('points', 0)
        away_score = away_record.get('points', 0)
        point_diff = home_score - away_score
        
        if point_diff > 0:
            winner = 'home'
            self.stats['home_wins'] += 1
        elif point_diff < 0:
            winner = 'away'
            self.stats['away_wins'] += 1
        else:
            winner = 'tie'
        
        # Construire le match structuré
        game = {
            'game_id': game_id,
            'season': home_record.get('season', ''),
            'game_date': home_record.get('game_date', ''),
            'season_type': home_record.get('season_type', ''),
            'home_team_id': home_record.get('team_id'),
            'home_team_name': home_record.get('team_name', ''),
            'home_team_abbr': home_record.get('team_abbreviation', ''),
            'away_team_id': away_record.get('team_id'),
            'away_team_name': away_record.get('team_name', ''),
            'away_team_abbr': away_record.get('team_abbreviation', ''),
            'home_score': home_score,
            'away_score': away_score,
            'point_diff': point_diff,
            'winner': winner,
            'home_fg_pct': home_record.get('fg_pct'),
            'home_fg3_pct': home_record.get('fg3_pct'),
            'home_ft_pct': home_record.get('ft_pct'),
            'home_reb': home_record.get('reb'),
            'home_ast': home_record.get('ast'),
            'away_fg_pct': away_record.get('fg_pct'),
            'away_fg3_pct': away_record.get('fg3_pct'),
            'away_ft_pct': away_record.get('ft_pct'),
            'away_reb': away_record.get('reb'),
            'away_ast': away_record.get('ast'),
        }
        
        return game
    
    def _save_games(self, games: List[Dict]):
        """Sauvegarde les matchs structurés."""
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        output_file = self.output_path / "games_structured.json"
        
        output_data = {
            'data': games,
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'record_count': len(games),
                'source': 'nba20_transform_games',
                'ticket': 'NBA-20',
                'version': '1.0'
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Matchs sauvegardés: {output_file}")
    
    def _calculate_stats(self, games: List[Dict]):
        """Calcule les statistiques finales."""
        if not games:
            return
        
        # Calculer marge moyenne
        margins = [abs(g['point_diff']) for g in games]
        avg_margin = sum(margins) / len(margins)
        max_margin = max(margins) if margins else 0
        
        # Home win rate
        home_wins = sum(1 for g in games if g['winner'] == 'home')
        total = len(games)
        home_win_rate = (home_wins / total * 100) if total > 0 else 0
        
        logger.info(f"Marge moyenne: {avg_margin:.1f} points")
        logger.info(f"Marge max: {max_margin} points")
        logger.info(f"Home win rate: {home_win_rate:.1f}%")
        
        # Sauvegarder stats
        self.stats['avg_margin'] = avg_margin
        self.stats['max_margin'] = max_margin
        self.stats['home_win_rate'] = home_win_rate


if __name__ == "__main__":
    # Exécution standalone
    transformer = GamesTransformer()
    stats = transformer.transform_all()
    
    print("\n" + "=" * 60)
    print("RÉSULTATS NBA-20")
    print("=" * 60)
    print(f"Fichiers traités: {stats['total_files']}")
    print(f"Records bruts: {stats['total_records']}")
    print(f"Matchs structurés: {stats['unique_games']}")
    print(f"Home wins: {stats['home_wins']}")
    print(f"Away wins: {stats['away_wins']}")
    print(f"Home win rate: {stats.get('home_win_rate', 0):.1f}%")
    print(f"Marge moyenne: {stats.get('avg_margin', 0):.1f} points")
    print("=" * 60)
