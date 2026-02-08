#!/usr/bin/env python3
"""
NBA-23: Feature Engineering pour Archetypes de Joueurs
Version Refactorisée - Utilise BaseFeatureEngineer pour éviter la redondance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Ajoute le chemin src pour importer BaseFeatureEngineer
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ml.base.base_feature_engineer import BaseFeatureEngineer, NBAFormulasVectorized


class ArchetypeFeatureEngineer(BaseFeatureEngineer):
    """
    Ingénierie de features avancée pour clustering des archétypes NBA.
    Hérite de BaseFeatureEngineer pour réutiliser les formules NBA standardisées.
    """
    
    def __init__(self):
        super().__init__()
        self.formulas = NBAFormulasVectorized()
        
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée toutes les features pour le clustering en utilisant les méthodes héritées.
        """
        df = df.copy()
        
        # Renomme colonnes si nécessaire (NBA-18 format)
        column_mapping = {
            'full_name': 'player_name',
            'id': 'player_id'
        }
        for old, new in column_mapping.items():
            if old in df.columns and new not in df.columns:
                df[new] = df[old]
        
        # 1. Features physiques (utilise méthodes héritées)
        df = self._engineer_physical_features(df)
        
        # 2. Features offensives (normalisées par 36 min)
        df = self._engineer_offensive_features(df)
        
        # 3. Features défensives (normalisées par 36 min)
        df = self._engineer_defensive_features(df)
        
        # 4. Features de style de jeu
        df = self._engineer_playstyle_features(df)
        
        # 5. Ratios métier clés
        df = self._engineer_key_ratios(df)
        
        # 6. Features avancées NBA
        df = self._engineer_advanced_features(df)
        
        # 7. NBA-23: Métriques avancées (AST%, STL%, etc.)
        df = self._engineer_nba23_advanced_metrics(df)
        
        return df
    
    def _engineer_physical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features physiques de base - utilise méthodes héritées"""
        # BMI (hérité de BaseFeatureEngineer)
        if 'bmi' not in df.columns:
            df['bmi'] = self.calculate_bmi(df)
            self.register_feature('bmi', 'physical', 'Indice de masse corporelle')
        
        # Envergure estimée (approximation NBA: height + 10cm en moyenne)
        df['wingspan_estimated'] = df['height_cm'] + 10
        self.register_feature('wingspan_estimated', 'physical', 'Envergure estimée (height + 10cm)')
        
        # Ratio poids/taille (indicateur de force)
        df['weight_height_ratio'] = df['weight_kg'] / df['height_cm']
        self.register_feature('weight_height_ratio', 'physical', 'Ratio poids/taille')
        
        return df
    
    def _engineer_offensive_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features offensives normalisées par 36 minutes - utilise normalize_per_36 hérité"""
        # Normalisation par 36 minutes (utilise méthode héritée)
        df['pts_per_36'] = self.normalize_per_36(df, 'pts')
        df['ast_per_36'] = self.normalize_per_36(df, 'ast')
        df['fga_per_36'] = self.normalize_per_36(df, 'fga')
        df['fta_per_36'] = self.normalize_per_36(df, 'fta')
        
        # True Shooting % (utilise méthode héritée)
        if 'ts_pct' not in df.columns or df['ts_pct'].isna().all():
            df['ts_pct'] = self.calculate_ts_pct(df)
        
        # Effective FG% (utilise méthode héritée)
        if 'efg_pct' not in df.columns or df['efg_pct'].isna().all():
            df['efg_pct'] = self.calculate_efg_pct(df)
        
        # Efficacité scoring
        df['pts_per_fga'] = np.where(df['fga_per_36'] > 0, 
                                      df['pts_per_36'] / df['fga_per_36'], 0)
        
        # Ratio assists/turnovers
        df['tov_per_36'] = self.normalize_per_36(df, 'tov')
        df['ast_to_ratio'] = np.where(df['tov_per_36'] > 0,
                                       df['ast_per_36'] / df['tov_per_36'], 
                                       df['ast_per_36'])
        
        self.features_created.extend([
            'pts_per_36', 'ast_per_36', 'fga_per_36', 'fta_per_36',
            'pts_per_fga', 'tov_per_36', 'ast_to_ratio'
        ])
        return df
    
    def _engineer_defensive_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features défensives normalisées par 36 minutes"""
        # Stats défensives
        df['reb_per_36'] = self.normalize_per_36(df, 'reb')
        df['stl_per_36'] = self.normalize_per_36(df, 'stl')
        df['blk_per_36'] = self.normalize_per_36(df, 'blk')
        df['pf_per_36'] = self.normalize_per_36(df, 'pf')
        
        # Split rebonds off/def si disponibles
        if 'oreb' in df.columns:
            df['oreb_per_36'] = self.normalize_per_36(df, 'oreb')
        if 'dreb' in df.columns:
            df['dreb_per_36'] = self.normalize_per_36(df, 'dreb')
        
        # Activity index (combinaison stl + blk)
        df['defensive_activity'] = df['stl_per_36'] + df['blk_per_36']
        
        # Physical dominance (rebonds + blocks par taille)
        df['rim_protection_index'] = (df['blk_per_36'] * df['reb_per_36']) / (df['height_cm'] / 100)
        
        self.features_created.extend([
            'reb_per_36', 'stl_per_36', 'blk_per_36', 'pf_per_36',
            'defensive_activity', 'rim_protection_index'
        ])
        return df
    
    def _engineer_playstyle_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features de style de jeu - utilise méthodes héritées pour FTR et 3PAr"""
        # 3-point rate (% de tirs à 3 pts)
        if 'fga' in df.columns and df['fga'].sum() > 0:
            df['three_pt_rate'] = np.where(df['fga'] > 0,
                                            df.get('fg3a', 0) / df['fga'], 0)
        else:
            df['three_pt_rate'] = 0
        
        # Free throw rate (utilise méthode héritée)
        df['ft_rate'] = self.formulas.calculate_ftr(df)
        
        # 3-Point Attempt Rate (utilise méthode héritée)
        df['3par'] = self.formulas.calculate_3par(df)
        
        # Usage rate (si disponible)
        if 'usg_pct' not in df.columns:
            df['usg_pct'] = df['fga_per_36'] / 20 * 100  # Approximation
        
        # Games played percentage (régularité)
        if 'games_played' in df.columns:
            df['games_played_pct'] = df['games_played'] / 82
        else:
            df['games_played_pct'] = 0.5
        
        # Minutes per game (utilisation)
        if 'games_played' in df.columns and 'minutes' in df.columns:
            df['minutes_per_game'] = np.where(df['games_played'] > 0,
                                               df['minutes'] / df['games_played'], 0)
        else:
            df['minutes_per_game'] = df.get('min', 0)
        
        self.features_created.extend([
            'three_pt_rate', 'ft_rate', '3par', 'usg_pct', 
            'games_played_pct', 'minutes_per_game'
        ])
        return df
    
    def _engineer_key_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ratios métier clés pour identifier les archétypes"""
        # 1. Offensive Load (charge offensive)
        df['offensive_load'] = df['pts_per_36'] * (df['usg_pct'] / 100)
        
        # 2. Playmaking Score (création de jeu)
        df['playmaking_score'] = df['ast_per_36'] * df['ast_to_ratio']
        
        # 3. Efficiency Index (efficacité relative)
        if 'per' in df.columns:
            df['efficiency_index'] = np.where(df['usg_pct'] > 0,
                                               df['per'] / df['usg_pct'], 0)
        else:
            # Utilise PER estimé de BaseFeatureEngineer
            per_est = self.calculate_per_estimated(df)
            df['efficiency_index'] = np.where(df['usg_pct'] > 0, per_est / df['usg_pct'], 0)
        
        # 4. Versatility Score (équilibre offense/défense)
        offensive_score = (df['pts_per_36'] / 30 + df['ast_per_36'] / 10) / 2
        defensive_score = (df['reb_per_36'] / 10 + df['defensive_activity'] / 3) / 2
        df['versatility_score'] = (offensive_score + defensive_score) / 2
        
        # 5. Shooting Preference (0 = inside, 1 = outside)
        df['shooting_preference'] = (df['three_pt_rate'] * 0.7 + 
                                      np.minimum(df['ft_rate'] / 0.5, 1) * 0.3)
        
        # 6. Big Man Index (taille + rebonds + blocks)
        df['big_man_index'] = ((df['height_cm'] - 200) / 30 + 
                                df['reb_per_36'] / 10 + 
                                df['blk_per_36'] / 2) / 3
        
        self.features_created.extend([
            'offensive_load', 'playmaking_score', 'efficiency_index',
            'versatility_score', 'shooting_preference', 'big_man_index'
        ])
        return df
    
    def _engineer_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features avancées basées sur PER et autres métriques"""
        # PER category (si PER disponible)
        if 'per' in df.columns:
            conditions = [
                df['per'] >= 25,
                df['per'] >= 20,
                df['per'] >= 15,
                df['per'] >= 10,
                df['per'] > 0
            ]
            choices = ['elite', 'star', 'starter', 'role_player', 'fringe']
            df['per_category'] = np.select(conditions, choices, default='unknown')
        
        # Shooting Efficiency Score
        df['shooting_efficiency'] = (df['ts_pct'] + df.get('efg_pct', df['ts_pct'])) / 2
        
        # Clutch Factor (approximation basée sur minutes et usage)
        df['clutch_factor'] = df['minutes_per_game'] * (df['usg_pct'] / 100) / 36
        
        # Consistency Score (basé sur games played et minutes)
        df['consistency_score'] = (df['games_played_pct'] * 0.5 + 
                                    np.minimum(df['minutes_per_game'] / 36, 1) * 0.5)
        
        self.features_created.extend([
            'shooting_efficiency', 'clutch_factor', 'consistency_score'
        ])
        return df
    
    def _engineer_nba23_advanced_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        NBA-23: Métriques avancées pour clustering avec vraies données équipe (NBA-19)
        """
        # Import des fonctions
        from src.utils.nba_formulas import (
            calculate_ast_pct, calculate_stl_pct, calculate_blk_pct,
            calculate_tov_pct, calculate_trb_pct, calculate_vorp_estimated,
            calculate_ws_per_48, calculate_ftr, calculate_3par
        )
        
        # Tente de charger les vraies stats d'équipe depuis NBA-19
        try:
            team_stats = self._load_team_stats()
            use_real_team_stats = True
        except:
            # Fallback sur approximations si NBA-19 non disponible
            team_stats = None
            use_real_team_stats = False
        
        minutes = df.get('minutes', pd.Series([0]*len(df)))
        
        if use_real_team_stats:
            # Utilise les vraies stats d'équipe de NBA-19
            df = self._calculate_advanced_metrics_with_team_stats(df, team_stats)
        else:
            # Approximation legacy (à remplacer par vraies données)
            team_minutes = minutes * 5
            team_fg = df.get('fgm', 0) * 5
            team_reb = df.get('reb', 0) * 5
            opp_reb = team_reb
            opp_poss = pd.Series([100]*len(df))
            opp_fga = df.get('fga', 0) * 5
            opp_3pa = df.get('fg3a', 0) * 5
            
            df['ast_pct'] = calculate_ast_pct(
                df.get('ast', 0), team_fg, df.get('fgm', 0), minutes, team_minutes
            )
            df['stl_pct'] = calculate_stl_pct(
                df.get('stl', 0), opp_poss, minutes, team_minutes
            )
            df['blk_pct'] = calculate_blk_pct(
                df.get('blk', 0), opp_fga, opp_3pa, minutes, team_minutes
            )
        
        # TOV% ne dépend pas des stats d'équipe
        df['tov_pct'] = calculate_tov_pct(
            df.get('tov', 0), df.get('fga', 0), df.get('fta', 0)
        )
        
        # TRB% utilise team_reb et opp_reb
        if use_real_team_stats:
            df['trb_pct'] = calculate_trb_pct(
                df.get('reb', 0), 
                df['team_reb'], 
                df['opp_reb'],
                minutes, 
                df['team_minutes']
            )
        else:
            df['trb_pct'] = calculate_trb_pct(
                df.get('reb', 0), team_reb, opp_reb, minutes, team_minutes
            )
        
        # VORP et WS/48 estimés à partir du PER
        df['vorp'] = calculate_vorp_estimated(df.get('per', 0), minutes)
        df['ws_per_48'] = calculate_ws_per_48(df.get('per', 0), minutes)
        
        # FTR et 3PAr déjà calculés dans _engineer_playstyle_features
        if 'ftr' not in df.columns:
            df['ftr'] = calculate_ftr(df.get('fta', 0), df.get('fga', 0))
        
        # Features de contexte
        if 'from_year' in df.columns and 'to_year' in df.columns:
            df['years_active'] = df['to_year'] - df['from_year']
        else:
            df['years_active'] = 5
        
        if 'games_played' in df.columns and 'games' in df.columns:
            df['starter_ratio'] = df['games'] / df['games_played'].clip(lower=1)
        else:
            df['starter_ratio'] = 0.5
        
        self.features_created.extend([
            'ast_pct', 'stl_pct', 'blk_pct', 'tov_pct', 'trb_pct',
            'vorp', 'ws_per_48', 'years_active', 'starter_ratio'
        ])
        
        return df
    
    def _load_team_stats(self) -> Optional[pd.DataFrame]:
        """Charge les stats d'équipe depuis NBA-19 pour des calculs précis"""
        import json
        from pathlib import Path
        
        team_stats_path = Path('data/gold/team_season_stats')
        if not team_stats_path.exists():
            return None
        
        # Charge toutes les stats d'équipe
        all_stats = []
        for file in team_stats_path.glob('*.json'):
            with open(file) as f:
                stats = json.load(f)
                all_stats.append(stats)
        
        if not all_stats:
            return None
        
        return pd.DataFrame(all_stats)
    
    def _calculate_advanced_metrics_with_team_stats(self, df: pd.DataFrame, team_stats: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques avancées avec vraies stats d'équipe de NBA-19"""
        from src.utils.nba_formulas import (
            calculate_ast_pct, calculate_stl_pct, calculate_blk_pct, calculate_trb_pct
        )
        
        # Agrège les stats d'équipe (moyenne sur toutes les équipes/saisons)
        avg_team_fg = team_stats['field_goals_made'].mean() if 'field_goals_made' in team_stats.columns else None
        avg_team_reb = team_stats['rebounds'].mean() if 'rebounds' in team_stats.columns else None
        avg_team_poss = team_stats.get('possessions', pd.Series([100]*len(team_stats))).mean()
        
        minutes = df.get('minutes', pd.Series([0]*len(df)))
        team_minutes = minutes * 5  # Minutes de l'équipe quand le joueur joue
        
        # Pour chaque joueur, trouve les stats de son équipe si disponible
        if 'team_id' in df.columns and avg_team_fg:
            # Mapping team_id -> stats réelles
            team_stats_dict = team_stats.set_index('team_id').to_dict('index') if 'team_id' in team_stats.columns else {}
            
            # Utilise stats réelles si disponibles, sinon moyennes
            df['team_fg'] = df['team_id'].map(lambda x: team_stats_dict.get(x, {}).get('field_goals_made', avg_team_fg))
            df['team_reb'] = df['team_id'].map(lambda x: team_stats_dict.get(x, {}).get('rebounds', avg_team_reb))
            df['team_minutes'] = team_minutes
        else:
            # Fallback sur moyennes globales
            df['team_fg'] = avg_team_fg if avg_team_fg else df.get('fgm', 0) * 5
            df['team_reb'] = avg_team_reb if avg_team_reb else df.get('reb', 0) * 5
            df['team_minutes'] = team_minutes
        
        # Stats adverses (approximation: même niveau)
        df['opp_reb'] = df['team_reb']
        df['opp_poss'] = avg_team_poss if avg_team_poss else 100
        df['opp_fga'] = team_stats['field_goals_attempted'].mean() if 'field_goals_attempted' in team_stats.columns else df.get('fga', 0) * 5
        df['opp_3pa'] = team_stats['three_pointers_attempted'].mean() if 'three_pointers_attempted' in team_stats.columns else df.get('fg3a', 0) * 5
        
        # Calcule les métriques avec vraies données
        df['ast_pct'] = calculate_ast_pct(
            df.get('ast', 0), df['team_fg'], df.get('fgm', 0), minutes, df['team_minutes']
        )
        
        df['stl_pct'] = calculate_stl_pct(
            df.get('stl', 0), df['opp_poss'], minutes, df['team_minutes']
        )
        
        df['blk_pct'] = calculate_blk_pct(
            df.get('blk', 0), df['opp_fga'], df['opp_3pa'], minutes, df['team_minutes']
        )
        
        return df
    
    def get_feature_list(self, include_raw: bool = False) -> List[str]:
        """
        Retourne la liste des features pour clustering.
        Utilise le registre de features créées par register_feature().
        """
        # Utilise les features créées + quelques features brutes importantes
        engineered = list(set(self.features_created))
        
        if include_raw:
            raw_features = ['per', 'pts', 'reb', 'ast', 'stl', 'blk']
            return list(set(engineered + raw_features))
        
        return engineered
    
    def prepare_for_clustering(self, df: pd.DataFrame, 
                               min_games: int = 10) -> pd.DataFrame:
        """
        Prépare les données finales pour le clustering.
        """
        # Features engineering
        df = self.engineer_features(df)
        
        # Filtre minimum
        if 'games_played' in df.columns:
            df = df[df['games_played'] >= min_games]
        
        # Supprime les joueurs sans stats offensives
        df = df[df['pts_per_36'] > 0]
        
        # Sélectionne les colonnes pour clustering
        feature_cols = self.get_feature_list(include_raw=False)
        available_cols = [col for col in feature_cols if col in df.columns]
        
        # Ajoute metadata
        metadata_cols = ['player_id', 'player_name', 'team_id', 'is_active', 'position']
        available_metadata = [col for col in metadata_cols if col in df.columns]
        
        # Garde lignes avec au moins 80% des features
        df_subset = df[available_cols + available_metadata]
        min_features = int(len(available_cols) * 0.8)
        df_clean = df_subset.dropna(thresh=min_features + len(available_metadata))
        
        # Remplit les NaN restants avec la médiane
        for col in available_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
        
        print(f"OK: {len(df_clean)} joueurs avec données complètes")
        print(f"OK: {len(available_cols)} features disponibles")
        
        return df_clean, available_cols, available_metadata


if __name__ == "__main__":
    # Test
    print("NBA-23 Feature Engineering Refactorisé - Test")
    
    # Crée données test
    test_data = {
        'player_id': [1, 2, 3],
        'player_name': ['Player A', 'Player B', 'Player C'],
        'height_cm': [201, 198, 211],
        'weight_kg': [102, 95, 115],
        'pts': [1500, 800, 400],
        'reb': [400, 600, 900],
        'ast': [300, 200, 100],
        'stl': [80, 120, 40],
        'blk': [30, 80, 200],
        'minutes': [2000, 1800, 1500],
        'games_played': [70, 65, 50],
        'fga': [1200, 600, 300],
        'fgm': [550, 280, 140],
        'fg3a': [400, 200, 20],
        'fta': [300, 150, 80]
    }
    
    df_test = pd.DataFrame(test_data)
    
    engineer = ArchetypeFeatureEngineer()
    df_result, features, metadata = engineer.prepare_for_clustering(df_test)
    
    print(f"\nFeatures créées: {len(features)}")
    print(f"Exemples: {features[:5]}")
    print(f"\nDonnées finales shape: {df_result.shape}")
    print(f"\nDocumentation des features:")
    print(engineer.get_feature_documentation().head())
