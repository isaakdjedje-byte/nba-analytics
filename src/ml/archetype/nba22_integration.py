#!/usr/bin/env python3
"""
NBA-23 vers NBA-22: Integration des features d'archetypes
Cree des features d'equipe basees sur les archetypes des joueurs
"""

import pandas as pd
import numpy as np
from scipy.stats import entropy


class ArchetypeTeamFeatures:
    """
    Cree des features d'equipe pour NBA-22 a partir des archetypes NBA-23
    """
    
    def __init__(self, player_archetypes_path='data/gold/player_archetypes/player_archetypes_v2.parquet'):
        """
        Args:
            player_archetypes_path: Chemin vers les donnees d'archetypes
        """
        self.player_archetypes = pd.read_parquet(player_archetypes_path)
        print(f"NBA-23 Integration: {len(self.player_archetypes)} joueurs charges")
    
    def create_team_features(self, team_ids=None):
        """
        Cree les features d'equipe
        
        Returns:
            DataFrame avec features par equipe
        """
        if team_ids is None:
            if 'team_id' in self.player_archetypes.columns:
                team_ids = self.player_archetypes['team_id'].unique()
            else:
                # Si pas de team_id, utilise player_id comme proxy
                print("WARNING: Pas de team_id, creation features par joueur")
                return self._create_player_features()
        
        team_features = []
        
        for team_id in team_ids:
            if pd.isna(team_id):
                continue
                
            team_data = self.player_archetypes[self.player_archetypes['team_id'] == team_id]
            
            if len(team_data) == 0:
                continue
            
            features = {
                'team_id': team_id,
                'n_players': len(team_data),
                
                # 1. Diversite d'archetypes
                'n_archetypes': team_data['archetype_id'].nunique(),
                'archetype_entropy': self._calculate_entropy(team_data['archetype_id']),
                
                # 2. Presence d'archetypes cles (binaires)
                'has_volume_scorer': int('VOLUME_SCORER' in team_data['archetype_id'].values),
                'has_energy_big': int('ENERGY_BIG' in team_data['archetype_id'].values),
                'has_role_player': int('ROLE_PLAYER' in team_data['archetype_id'].values),
                
                # 3. Distribution
                'role_player_pct': (team_data['archetype_id'] == 'ROLE_PLAYER').mean(),
                'volume_scorer_pct': (team_data['archetype_id'] == 'VOLUME_SCORER').mean(),
                'energy_big_pct': (team_data['archetype_id'] == 'ENERGY_BIG').mean(),
                
                # 4. Qualite
                'avg_per': team_data['per'].mean() if 'per' in team_data.columns else 0,
                'max_per': team_data['per'].max() if 'per' in team_data.columns else 0,
                'std_per': team_data['per'].std() if 'per' in team_data.columns else 0,
                
                # 5. Diversite de style
                'avg_ts_pct': team_data['ts_pct'].mean() if 'ts_pct' in team_data.columns else 0,
                'avg_usg_pct': team_data['usg_pct'].mean() if 'usg_pct' in team_data.columns else 0,
            }
            
            team_features.append(features)
        
        return pd.DataFrame(team_features)
    
    def _calculate_entropy(self, series):
        """Entropie de Shannon pour mesurer la diversite"""
        if len(series) == 0:
            return 0.0
        probs = series.value_counts(normalize=True)
        return entropy(probs) if len(probs) > 1 else 0.0
    
    def _create_player_features(self):
        """Fallback: cree features par joueur si pas de team_id"""
        df = self.player_archetypes.copy()
        
        # Ajoute features individuelles enrichies
        df['is_volume_scorer'] = (df['archetype_id'] == 'VOLUME_SCORER').astype(int)
        df['is_energy_big'] = (df['archetype_id'] == 'ENERGY_BIG').astype(int)
        df['is_role_player'] = (df['archetype_id'] == 'ROLE_PLAYER').astype(int)
        
        return df


if __name__ == "__main__":
    # Test
    print("NBA-23 vers NBA-22: Integration")
    
    integrator = ArchetypeTeamFeatures()
    team_features = integrator.create_team_features()
    
    print(f"\nFeatures creees pour {len(team_features)} equipes")
    print(f"Colonnes: {list(team_features.columns)}")
    
    if len(team_features) > 0:
        print("\nExemple:")
        print(team_features.head())
