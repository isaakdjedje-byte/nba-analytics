#!/usr/bin/env python3
"""
Tests pour NBA-21 Feature Engineering
Validation des features et detection de data leakage
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


class TestNBA21Features:
    """Tests pour valider la qualite des features NBA-21."""
    
    @pytest.fixture
    def features_df(self):
        """Charge le dataset de features."""
        features_file = Path("data/gold/ml_features/features_all.parquet")
        if not features_file.exists():
            pytest.skip("Features file not found")
        return pd.read_parquet(features_file)
    
    def test_data_loaded(self, features_df):
        """Verifie que les donnees sont chargees."""
        assert len(features_df) > 0
        print(f"\nTotal records: {len(features_df)}")
    
    def test_no_null_target(self, features_df):
        """La target ne doit pas avoir de valeurs nulles."""
        null_count = features_df['target'].isnull().sum()
        assert null_count == 0, f"Target has {null_count} null values"
    
    def test_target_distribution(self, features_df):
        """Distribution de la target doit etre raisonnable (home advantage)."""
        home_win_rate = features_df['target'].mean()
        # Home win rate should be between 50% and 65% (NBA home advantage)
        assert 0.50 <= home_win_rate <= 0.65, \
            f"Home win rate {home_win_rate:.3f} outside expected range [0.50, 0.65]"
        print(f"\nHome win rate: {home_win_rate:.3f}")
    
    def test_no_data_leakage_h2h(self, features_df):
        """
        Test critique: Pas de fuite de donnees dans H2H.
        h2h_home_win_rate doit etre 0.5 pour les premieres rencontres.
        """
        first_meetings = features_df[features_df['h2h_games'] == 0]
        if len(first_meetings) > 0:
            # Should be neutral (0.5) for first meetings
            h2h_rate = first_meetings['h2h_home_win_rate'].unique()
            assert len(h2h_rate) == 1 and h2h_rate[0] == 0.5, \
                "H2H rate should be 0.5 for first meetings"
        
        print(f"\nFirst meetings: {len(first_meetings)}")
        print(f"Games with H2H history: {(features_df['h2h_games'] > 0).sum()}")
    
    def test_temporal_consistency(self, features_df):
        """Les donnees doivent etre ordonnees chronologiquement."""
        # Check that for each season, games are ordered by date
        for season in features_df['season'].unique():
            season_df = features_df[features_df['season'] == season]
            dates = pd.to_datetime(season_df['game_date'])
            assert dates.is_monotonic_increasing, \
                f"Season {season} not in chronological order"
    
    def test_feature_ranges(self, features_df):
        """Les features doivent avoir des ranges coherents."""
        # Win percentages should be between 0 and 100
        assert features_df['home_win_pct'].between(0, 100).all()
        assert features_df['away_win_pct'].between(0, 100).all()
        
        # H2H home win rate should be between 0 and 1
        assert features_df['h2h_home_win_rate'].between(0, 1).all()
        
        # Rest days should be positive (can be high for offseason/breaks)
        assert (features_df['home_rest_days'] >= 0).all()
        assert (features_df['away_rest_days'] >= 0).all()
        
        print("\nAll feature ranges valid")
    
    def test_home_away_balance(self, features_df):
        """Chaque match doit avoir exactement une equipe home et une away."""
        # Check that home_team_id != away_team_id for all games
        same_team = (features_df['home_team_id'] == features_df['away_team_id']).sum()
        assert same_team == 0, f"{same_team} games have same home/away team"
    
    def test_point_diff_consistency(self, features_df):
        """Point diff doit correspondre a home_score - away_score."""
        calculated_diff = features_df['home_score'] - features_df['away_score']
        assert (features_df['point_diff'] == calculated_diff).all()
    
    def test_target_consistency(self, features_df):
        """Target doit correspondre au gagnant."""
        # target = 1 when home wins (point_diff > 0)
        target_from_diff = (features_df['point_diff'] > 0).astype(int)
        assert (features_df['target'] == target_from_diff).all()
    
    def test_required_features_exist(self, features_df):
        """Toutes les features requises doivent exister."""
        required_features = [
            'game_id', 'season', 'game_date',
            'home_team_id', 'away_team_id',
            'home_score', 'away_score',
            'home_win_pct', 'away_win_pct',
            'h2h_home_win_rate', 'h2h_games',
            'target'
        ]
        
        missing = [f for f in required_features if f not in features_df.columns]
        assert len(missing) == 0, f"Missing features: {missing}"
        
        print(f"\nAll {len(required_features)} required features present")
    
    def test_multiple_seasons(self, features_df):
        """Doit contenir plusieurs saisons pour le split temporel."""
        seasons = features_df['season'].nunique()
        assert seasons >= 2, f"Only {seasons} season(s) found, need at least 2"
        print(f"\nSeasons available: {seasons}")
        for season in sorted(features_df['season'].unique()):
            count = (features_df['season'] == season).sum()
            print(f"  {season}: {count} games")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
