#!/usr/bin/env python3
"""
NBA-23 Integration CORRIGEE
Mappe les archetypes joueurs vers les equipes via les rosters
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import json
from scipy.stats import entropy
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging = logging.getLogger(__name__)


class NBA23TeamIntegration:
    """
    Integre NBA-23 en mappant les joueurs vers les equipes via rosters
    """
    
    def __init__(self, season='2025-26'):
        self.season = season
        self.archetypes = None
        self.rosters = None
        self.team_features = None
        
    def load_archetypes(self):
        """Charge les archetypes des joueurs"""
        path = Path('data/gold/player_archetypes/player_archetypes_v2.parquet')
        if not path.exists():
            raise FileNotFoundError(f"Archetypes non trouves: {path}")
        
        self.archetypes = pd.read_parquet(path)
        logging.info(f"Archetypes charges: {len(self.archetypes)} joueurs")
        return self.archetypes
    
    def load_rosters(self):
        """Charge les rosters des equipes"""
        path = Path('data/gold/nba19/team_season_rosters.json')
        if not path.exists():
            raise FileNotFoundError(f"Rosters non trouves: {path}")
        
        with open(path) as f:
            data = json.load(f)
        
        # Filtrer par saison
        season_rosters = [r for r in data['data'] if r['season'] == self.season]
        
        self.rosters = season_rosters
        logging.info(f"Rosters {self.season}: {len(season_rosters)} equipes")
        return season_rosters
    
    def create_team_archetype_features(self):
        """
        Cree les features d'equipe basees sur les archetypes des joueurs
        """
        if self.archetypes is None:
            self.load_archetypes()
        if self.rosters is None:
            self.load_rosters()
        
        logging.info(f"\nCreation features equipe {self.season}...")
        
        team_features_list = []
        
        for roster in self.rosters:
            team_id = roster['team_id']
            players = roster['players']
            
            # Recuperer les archetypes des joueurs de l'equipe
            player_ids = [p['player_id'] for p in players]
            team_players = self.archetypes[self.archetypes['player_id'].isin(player_ids)]
            
            if len(team_players) == 0:
                logging.warning(f"Team {team_id}: aucun joueur trouve dans archetypes")
                continue
            
            # Features d'equipe
            features = {
                'team_id': team_id,
                'season': self.season,
                'n_players': len(team_players),
                
                # Diversite d'archetypes
                'n_archetypes': team_players['archetype_id'].nunique(),
                'archetype_entropy': self._calculate_entropy(team_players['archetype_id']),
                
                # Presence archetypes cles
                'has_volume_scorer': int('VOLUME_SCORER' in team_players['archetype_id'].values),
                'has_energy_big': int('ENERGY_BIG' in team_players['archetype_id'].values),
                'has_role_player': int('ROLE_PLAYER' in team_players['archetype_id'].values),
                
                # Distribution
                'role_player_pct': (team_players['archetype_id'] == 'ROLE_PLAYER').mean(),
                'volume_scorer_pct': (team_players['archetype_id'] == 'VOLUME_SCORER').mean(),
                'energy_big_pct': (team_players['archetype_id'] == 'ENERGY_BIG').mean(),
                
                # Qualite
                'avg_per': team_players['per'].mean() if 'per' in team_players.columns else 0,
                'max_per': team_players['per'].max() if 'per' in team_players.columns else 0,
                'std_per': team_players['per'].std() if 'per' in team_players.columns else 0,
                
                # Style de jeu
                'avg_ts_pct': team_players['ts_pct'].mean() if 'ts_pct' in team_players.columns else 0,
                'avg_usg_pct': team_players['usg_pct'].mean() if 'usg_pct' in team_players.columns else 0,
                'avg_efficiency': team_players['efficiency_index'].mean() if 'efficiency_index' in team_players.columns else 0,
            }
            
            team_features_list.append(features)
        
        self.team_features = pd.DataFrame(team_features_list)
        logging.info(f"Features creees pour {len(self.team_features)} equipes")
        
        return self.team_features
    
    def _calculate_entropy(self, series):
        """Entropie de Shannon"""
        if len(series) == 0:
            return 0.0
        probs = series.value_counts(normalize=True)
        return entropy(probs) if len(probs) > 1 else 0.0
    
    def merge_with_match_features(self, match_df):
        """
        Merge les features d'equipe avec les features de match
        """
        if self.team_features is None:
            self.create_team_archetype_features()
        
        logging.info("\nMerge avec features de match...")
        
        # Merge pour equipe a domicile
        df = match_df.merge(
            self.team_features,
            left_on='home_team_id',
            right_on='team_id',
            how='left',
            suffixes=('', '_home_arch')
        )
        
        # Merge pour equipe exterieur
        df = df.merge(
            self.team_features,
            left_on='away_team_id',
            right_on='team_id',
            how='left',
            suffixes=('', '_away_arch')
        )
        
        # Supprimer colonnes dupliquees
        df = df.drop(columns=['team_id_home_arch', 'team_id_away_arch'], errors='ignore')
        
        n_new_features = len([c for c in df.columns if '_arch' in c])
        logging.info(f"✅ {n_new_features} features NBA-23 integrees")
        
        return df
    
    def save_team_features(self, output_path=None):
        """Sauvegarde les features d'equipe"""
        if self.team_features is None:
            self.create_team_archetype_features()
        
        if output_path is None:
            output_path = f'data/gold/nba23_team_features_{self.season}.parquet'
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.team_features.to_parquet(output_path)
        logging.info(f"Features sauvegardees: {output_path}")
        
        return output_path


if __name__ == "__main__":
    integration = NBA23TeamIntegration(season='2025-26')
    
    try:
        features = integration.create_team_archetype_features()
        print(f"\n{'='*70}")
        print("NBA-23 INTEGRATION")
        print(f"{'='*70}")
        print(f"Equipes: {len(features)}")
        print(f"Features: {len(features.columns)}")
        print("\nApercu:")
        print(features[['team_id', 'n_archetypes', 'has_volume_scorer', 'avg_per']].head())
        
        # Sauvegarder
        integration.save_team_features()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
