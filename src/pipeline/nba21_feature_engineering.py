#!/usr/bin/env python3
"""
NBA-21: Feature Engineering Pipeline - 10x Engineer Mode
Transforms games_enriched (box score format) to matchup format with ML features
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NBA21FeatureEngineer:
    """
    Professional feature engineering pipeline for NBA match prediction.
    
    Transforms box score data (2 records per game) into matchup format 
    (1 record per game) with engineered features for ML.
    """
    
    def __init__(self, exports_dir: str = "data/exports"):
        self.exports_dir = Path(exports_dir)
        self.games_df = None
        self.matchup_df = None
        self.stats = {}
        
    def load_all_seasons(self) -> pd.DataFrame:
        """Load all parquet files from exports directory."""
        logger.info("Loading all seasons from exports...")
        
        parquet_files = list(self.exports_dir.glob("games_*.parquet/*.parquet"))
        logger.info(f"Found {len(parquet_files)} parquet files")
        
        dfs = []
        for file in sorted(parquet_files):
            try:
                df = pd.read_parquet(file)
                season = file.parent.name.replace('games_', '').replace('_', '-')
                df['source_file'] = season
                dfs.append(df)
                logger.info(f"  Loaded {file.parent.name}: {len(df)} records")
            except Exception as e:
                logger.warning(f"  Failed to load {file}: {e}")
        
        self.games_df = pd.concat(dfs, ignore_index=True)
        
        # Clean season format
        self.games_df['season'] = self.games_df['season'].astype(str)
        
        self.stats['total_records'] = len(self.games_df)
        self.stats['unique_games'] = self.games_df['game_id'].nunique()
        self.stats['seasons'] = self.games_df['season'].unique().tolist()
        
        logger.info(f"Total loaded: {self.stats['total_records']} records, "
                   f"{self.stats['unique_games']} unique games")
        logger.info(f"Seasons: {', '.join(sorted(self.stats['seasons']))}")
        
        return self.games_df
    
    def transform_to_matchup(self) -> pd.DataFrame:
        """
        Transform box score format (2 rows/game) to matchup format (1 row/game).
        """
        logger.info("Transforming to matchup format...")
        
        if self.games_df is None:
            raise ValueError("Call load_all_seasons() first")
        
        # Separate home and away teams
        home_df = self.games_df[self.games_df['is_home'] == True].copy()
        away_df = self.games_df[self.games_df['is_home'] == False].copy()
        
        logger.info(f"Home records: {len(home_df)}, Away records: {len(away_df)}")
        
        # Rename columns with prefixes
        home_cols = {
            'team_id': 'home_team_id',
            'team_name': 'home_team_name',
            'team_abbr': 'home_team_abbr',
            'points': 'home_score',
            'WL': 'home_wl',
            'avg_points_last_5': 'home_avg_pts_last_5',
            'avg_points_last_10': 'home_avg_pts_last_10',
            'avg_points_last_20': 'home_avg_pts_last_20',
            'avg_reb_last_5': 'home_avg_reb_last_5',
            'avg_ast_last_5': 'home_avg_ast_last_5',
            'win_pct': 'home_win_pct',
            'win_pct_last_5': 'home_win_pct_last_5',
            'wins_last_10': 'home_wins_last_10',
            'days_rest': 'home_rest_days',
            'is_back_to_back': 'home_is_back_to_back',
            'ts_pct': 'home_ts_pct',
            'efg_pct': 'home_efg_pct',
            'game_score': 'home_game_score',
            'trend_vs_season': 'home_trend',
            'avg_points_season': 'home_avg_pts_season',
            'fatigue_efficiency': 'home_fatigue_eff',
            'fg_pct': 'home_fg_pct',
            'fg3_pct': 'home_fg3_pct',
            'ft_pct': 'home_ft_pct',
            'reb': 'home_reb',
            'ast': 'home_ast',
            'stl': 'home_stl',
            'blk': 'home_blk',
            'tov': 'home_tov',
            'pf': 'home_pf',
        }
        
        away_cols = {
            'team_id': 'away_team_id',
            'team_name': 'away_team_name',
            'team_abbr': 'away_team_abbr',
            'points': 'away_score',
            'WL': 'away_wl',
            'avg_points_last_5': 'away_avg_pts_last_5',
            'avg_points_last_10': 'away_avg_pts_last_10',
            'avg_points_last_20': 'away_avg_pts_last_20',
            'avg_reb_last_5': 'away_avg_reb_last_5',
            'avg_ast_last_5': 'away_avg_ast_last_5',
            'win_pct': 'away_win_pct',
            'win_pct_last_5': 'away_win_pct_last_5',
            'wins_last_10': 'away_wins_last_10',
            'days_rest': 'away_rest_days',
            'is_back_to_back': 'away_is_back_to_back',
            'ts_pct': 'away_ts_pct',
            'efg_pct': 'away_efg_pct',
            'game_score': 'away_game_score',
            'trend_vs_season': 'away_trend',
            'avg_points_season': 'away_avg_pts_season',
            'fatigue_efficiency': 'away_fatigue_eff',
            'fg_pct': 'away_fg_pct',
            'fg3_pct': 'away_fg3_pct',
            'ft_pct': 'away_ft_pct',
            'reb': 'away_reb',
            'ast': 'away_ast',
            'stl': 'away_stl',
            'blk': 'away_blk',
            'tov': 'away_tov',
            'pf': 'away_pf',
        }
        
        # Apply renaming (only for columns that exist)
        home_df = home_df.rename(columns={k: v for k, v in home_cols.items() if k in home_df.columns})
        away_df = away_df.rename(columns={k: v for k, v in away_cols.items() if k in away_df.columns})
        
        # Keep only necessary columns for merge
        merge_cols = ['game_id', 'season', 'game_date', 'season_type']
        home_cols_present = [c for c in home_df.columns if c.startswith('home_')]
        away_cols_present = [c for c in away_df.columns if c.startswith('away_')]
        
        home_merge = home_df[merge_cols + home_cols_present].copy()
        away_merge = away_df[merge_cols + away_cols_present].copy()
        
        # Merge on game_id
        self.matchup_df = pd.merge(
            home_merge, away_merge, 
            on=['game_id', 'season', 'game_date', 'season_type'],
            how='inner',
            suffixes=('', '_away')
        )
        
        # Calculate point differential
        self.matchup_df['point_diff'] = (
            self.matchup_df['home_score'] - self.matchup_df['away_score']
        )
        
        # Create target variable (1 if home wins, 0 if away wins)
        self.matchup_df['target'] = (
            self.matchup_df['point_diff'] > 0
        ).astype(int)
        
        # Calculate overtime flag (if available)
        if 'overtime' in self.matchup_df.columns:
            self.matchup_df['is_overtime'] = self.matchup_df['overtime'].fillna(False).astype(int)
        
        self.stats['matchup_records'] = len(self.matchup_df)
        logger.info(f"Created {self.stats['matchup_records']} matchup records")
        
        return self.matchup_df
    
    def calculate_h2h_features(self) -> pd.DataFrame:
        """
        Calculate head-to-head historical features.
        CRITICAL: Only uses data BEFORE current game to avoid data leakage.
        """
        logger.info("Calculating H2H features...")
        
        if self.matchup_df is None:
            raise ValueError("Call transform_to_matchup() first")
        
        # Sort by date to ensure temporal order
        self.matchup_df = self.matchup_df.sort_values(['season', 'game_date']).reset_index(drop=True)
        
        # Initialize H2H columns
        self.matchup_df['h2h_games'] = 0
        self.matchup_df['h2h_home_wins'] = 0
        self.matchup_df['h2h_home_win_rate'] = 0.5  # Neutral prior
        self.matchup_df['h2h_avg_margin'] = 0.0
        
        # Calculate H2H for each pair
        for idx, row in self.matchup_df.iterrows():
            home_id = row['home_team_id']
            away_id = row['away_team_id']
            current_date = row['game_date']
            
            # Find previous games between these teams (either home/away combination)
            h2h_games = self.matchup_df[
                (self.matchup_df.index < idx) &  # BEFORE current game
                (
                    ((self.matchup_df['home_team_id'] == home_id) & (self.matchup_df['away_team_id'] == away_id)) |
                    ((self.matchup_df['home_team_id'] == away_id) & (self.matchup_df['away_team_id'] == home_id))
                )
            ]
            
            if len(h2h_games) > 0:
                # Count games where home_id was home team
                home_as_home = h2h_games[
                    (h2h_games['home_team_id'] == home_id)
                ]
                home_wins_as_home = (home_as_home['target'] == 1).sum()
                
                # Count games where home_id was away team  
                home_as_away = h2h_games[
                    (h2h_games['away_team_id'] == home_id)
                ]
                home_wins_as_away = (home_as_away['target'] == 0).sum()  # Away win means home_id won
                
                total_games = len(h2h_games)
                total_home_wins = home_wins_as_home + home_wins_as_away
                
                self.matchup_df.at[idx, 'h2h_games'] = total_games
                self.matchup_df.at[idx, 'h2h_home_wins'] = total_home_wins
                self.matchup_df.at[idx, 'h2h_home_win_rate'] = total_home_wins / total_games
                self.matchup_df.at[idx, 'h2h_avg_margin'] = h2h_games['point_diff'].mean()
        
        # Handle first meetings (no H2H history)
        self.matchup_df['h2h_home_win_rate'] = self.matchup_df['h2h_home_win_rate'].fillna(0.5)
        self.matchup_df['h2h_avg_margin'] = self.matchup_df['h2h_avg_margin'].fillna(0)
        
        h2h_stats = {
            'games_with_h2h': (self.matchup_df['h2h_games'] > 0).sum(),
            'avg_h2h_games': self.matchup_df['h2h_games'].mean(),
            'avg_h2h_home_win_rate': self.matchup_df['h2h_home_win_rate'].mean()
        }
        
        logger.info(f"H2H stats: {h2h_stats}")
        self.stats.update(h2h_stats)
        
        return self.matchup_df
    
    def create_feature_interactions(self) -> pd.DataFrame:
        """Create interaction features between home and away."""
        logger.info("Creating feature interactions...")
        
        # Rest advantage (always available)
        self.matchup_df['rest_advantage'] = (
            self.matchup_df['home_rest_days'] - self.matchup_df['away_rest_days']
        )
        
        # Win percentage differential
        if 'home_win_pct' in self.matchup_df.columns and 'away_win_pct' in self.matchup_df.columns:
            self.matchup_df['win_pct_diff'] = (
                self.matchup_df['home_win_pct'] - self.matchup_df['away_win_pct']
            )
        
        # Recent form differential (check if columns exist)
        if 'home_win_pct_last_5' in self.matchup_df.columns and 'away_win_pct_last_5' in self.matchup_df.columns:
            self.matchup_df['form_diff_last_5'] = (
                self.matchup_df['home_win_pct_last_5'] - self.matchup_df['away_win_pct_last_5']
            )
        
        # Points differential
        if 'home_avg_pts_last_5' in self.matchup_df.columns and 'away_avg_pts_last_5' in self.matchup_df.columns:
            self.matchup_df['pts_diff_last_5'] = (
                self.matchup_df['home_avg_pts_last_5'] - self.matchup_df['away_avg_pts_last_5']
            )
        
        # Efficiency differential
        if 'home_ts_pct' in self.matchup_df.columns and 'away_ts_pct' in self.matchup_df.columns:
            self.matchup_df['ts_pct_diff'] = (
                self.matchup_df['home_ts_pct'] - self.matchup_df['away_ts_pct']
            )
        
        # Trend differential
        if 'home_trend' in self.matchup_df.columns and 'away_trend' in self.matchup_df.columns:
            self.matchup_df['trend_diff'] = (
                self.matchup_df['home_trend'] - self.matchup_df['away_trend']
            )
        
        logger.info(f"Created interaction features: {[c for c in self.matchup_df.columns if any(x in c for x in ['diff', 'advantage'])]}")
        
        return self.matchup_df
    
    def get_feature_columns(self) -> List[str]:
        """Get list of ML feature columns."""
        exclude_cols = [
            'game_id', 'season', 'game_date', 'season_type',
            'home_team_id', 'home_team_name', 'home_team_abbr',
            'away_team_id', 'away_team_name', 'away_team_abbr',
            'home_wl', 'away_wl', 'target'
        ]
        
        feature_cols = [c for c in self.matchup_df.columns if c not in exclude_cols]
        return feature_cols
    
    def validate_features(self) -> Dict:
        """Validate feature quality and report statistics."""
        logger.info("Validating features...")
        
        validation = {
            'total_records': len(self.matchup_df),
            'target_distribution': self.matchup_df['target'].value_counts().to_dict(),
            'home_win_rate': self.matchup_df['target'].mean(),
            'null_counts': self.matchup_df.isnull().sum().sum(),
            'features_count': len(self.get_feature_columns())
        }
        
        # Check for data leakage
        if 'future_feature' in self.matchup_df.columns:
            validation['warning'] = 'Potential data leakage detected!'
        
        logger.info(f"Validation: {validation['total_records']} records, "
                   f"{validation['features_count']} features, "
                   f"home win rate: {validation['home_win_rate']:.3f}")
        
        return validation
    
    def save_features(self, output_dir: str = "data/gold/ml_features"):
        """Save features to parquet format partitioned by season."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving features to {output_path}...")
        
        # Save as parquet with season partitioning
        for season in self.matchup_df['season'].unique():
            season_df = self.matchup_df[self.matchup_df['season'] == season]
            season_file = output_path / f"features_{season}.parquet"
            season_df.to_parquet(season_file, index=False)
            logger.info(f"  Saved {season}: {len(season_df)} records to {season_file}")
        
        # Also save full dataset
        full_file = output_path / "features_all.parquet"
        self.matchup_df.to_parquet(full_file, index=False)
        logger.info(f"  Saved full dataset: {len(self.matchup_df)} records to {full_file}")
        
        # Save metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'total_records': len(self.matchup_df),
            'total_features': len(self.get_feature_columns()),
            'seasons': sorted(self.matchup_df['season'].unique().tolist()),
            'feature_columns': self.get_feature_columns(),
            'stats': self.stats
        }
        
        import json
        with open(output_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Saved metadata to {output_path / 'metadata.json'}")
        
    def run_pipeline(self) -> pd.DataFrame:
        """Run complete NBA-21 feature engineering pipeline."""
        logger.info("="*70)
        logger.info("NBA-21 FEATURE ENGINEERING PIPELINE - 10x MODE")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        # Execute pipeline steps
        self.load_all_seasons()
        self.transform_to_matchup()
        self.calculate_h2h_features()
        self.create_feature_interactions()
        self.validate_features()
        self.save_features()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("="*70)
        logger.info(f"Pipeline completed in {elapsed:.2f}s")
        logger.info(f"Output: {self.stats['matchup_records']} matchup records "
                   f"with {len(self.get_feature_columns())} features")
        logger.info("="*70)
        
        return self.matchup_df


def main():
    """Main execution function."""
    engineer = NBA21FeatureEngineer()
    
    try:
        df = engineer.run_pipeline()
        
        # Display sample
        print("\n" + "="*70)
        print("SAMPLE FEATURES")
        print("="*70)
        sample_cols = ['game_id', 'season']
        if 'home_team_name' in df.columns:
            sample_cols.extend(['home_team_name', 'away_team_name'])
        sample_cols.extend(['home_win_pct', 'away_win_pct', 'h2h_home_win_rate', 'target'])
        existing_cols = [c for c in sample_cols if c in df.columns]
        print(df[existing_cols].head(10).to_string())
        
        print("\n" + "="*70)
        print("FEATURE SUMMARY")
        print("="*70)
        print(f"Total features: {len(engineer.get_feature_columns())}")
        print(f"Feature categories:")
        print(f"  - Home stats: {len([c for c in engineer.get_feature_columns() if c.startswith('home_')])}")
        print(f"  - Away stats: {len([c for c in engineer.get_feature_columns() if c.startswith('away_')])}")
        print(f"  - H2H features: {len([c for c in engineer.get_feature_columns() if c.startswith('h2h_')])}")
        print(f"  - Interactions: {len([c for c in engineer.get_feature_columns() if 'diff' in c or 'advantage' in c])}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
