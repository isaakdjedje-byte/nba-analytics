"""
Tests intégration NBA-19 - Validation end-to-end

Vérifie que NBA-19 produit des données utilisables par NBA-20 et NBA-21.

Tests:
- Extraction des données
- Agrégations Team-Season
- Jointures Player-Team
- Validation ML-ready
- Stockage Gold

Ticket: NBA-19
"""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from processing.nba19_unified_aggregates import NBA19AggregationPipeline


class TestNBA19Extraction:
    """Tests Phase 1: Extraction"""
    
    def test_pipeline_initialization(self):
        """Vérifier que le pipeline s'initialise correctement"""
        pipeline = NBA19AggregationPipeline()
        assert pipeline is not None
        assert pipeline._cache == {}
        assert pipeline.stats['errors'] == 0
    
    def test_data_paths_exist(self):
        """Vérifier que les chemins de données sont configurés"""
        pipeline = NBA19AggregationPipeline()
        assert pipeline.players_path is not None
        assert pipeline.games_path is not None
        assert pipeline.teams_path is not None


class TestNBA19Transformations:
    """Tests Phase 2: Transformations"""
    
    def test_team_stats_structure(self):
        """Vérifier structure des agrégations équipe"""
        pipeline = NBA19AggregationPipeline()
        
        # Simuler données minimales
        pipeline._cache['games'] = [
            {
                'game_id': '001',
                'season': '2023-24',
                'home_team_id': 1,
                'home_team_name': 'Lakers',
                'away_team_id': 2,
                'away_team_name': 'Celtics',
                'home_score': 110,
                'away_score': 105,
                'winner': 'home',
                'home_reb': 45,
                'home_ast': 25,
                'home_fg_pct': 0.48,
                'away_reb': 40,
                'away_ast': 20,
                'away_fg_pct': 0.45
            }
        ]
        
        df = pipeline._transform_team_stats()
        
        assert not df.empty
        assert 'team_id' in df.columns
        assert 'team_name' in df.columns
        assert 'season' in df.columns
        assert 'games_played' in df.columns
        assert 'win_pct' in df.columns
        assert 'avg_pts_scored' in df.columns
    
    def test_player_team_join(self):
        """Vérifier jointures joueurs-équipes"""
        pipeline = NBA19AggregationPipeline()
        
        # Simuler données
        pipeline._cache['players'] = [
            {
                'player_id': 1,
                'full_name': 'LeBron James',
                'team_id': 1,
                'season': '2023-24',
                'position': 'F',
                'per': 25.5,
                'ts_pct': 0.62
            }
        ]
        
        pipeline._cache['teams'] = {
            1: {
                'id': 1,
                'full_name': 'Los Angeles Lakers',
                'conference': 'West',
                'division': 'Pacific',
                'city': 'Los Angeles'
            }
        }
        
        team_df = pd.DataFrame([
            {
                'team_id': 1,
                'team_name': 'Lakers',
                'season': '2023-24',
                'games_played': 10,
                'win_pct': 60.0,
                'avg_pts_scored': 115.5
            }
        ])
        
        df = pipeline._transform_player_team(team_df)
        
        assert not df.empty
        assert 'player_id' in df.columns
        assert 'conference' in df.columns
        assert 'division' in df.columns
        assert df.iloc[0]['conference'] == 'West'


class TestNBA19Validation:
    """Tests Phase 3: Validation ML-ready"""
    
    def test_team_count_validation(self):
        """Vérifier validation nombre d'équipes"""
        pipeline = NBA19AggregationPipeline()
        
        # Créer 30 équipes
        teams_data = []
        for i in range(30):
            teams_data.append({
                'team_id': i + 1,
                'team_name': f'Team_{i}',
                'season': '2023-24',
                'games_played': 82,
                'win_pct': 50.0,
                'avg_pts_scored': 115.0
            })
        
        team_df = pd.DataFrame(teams_data)
        player_df = pd.DataFrame()
        
        # Ne doit pas lever d'exception
        try:
            pipeline._validate_ml_ready(team_df, player_df)
            assert True
        except ValueError:
            pytest.fail("Validation ne devrait pas échouer avec 30 équipes")
    
    def test_invalid_team_count(self):
        """Vérifier détection nombre d'équipes invalide"""
        pipeline = NBA19AggregationPipeline()
        
        # Créer seulement 5 équipes
        team_df = pd.DataFrame([
            {
                'team_id': i,
                'team_name': f'Team_{i}',
                'season': '2023-24',
                'games_played': 82,
                'win_pct': 50.0,
                'avg_pts_scored': 115.0
            }
            for i in range(5)
        ])
        
        player_df = pd.DataFrame()
        
        # Doit lever une exception
        with pytest.raises(ValueError) as exc_info:
            pipeline._validate_ml_ready(team_df, player_df)
        
        assert "Nombre d'équipes" in str(exc_info.value)


class TestNBA19EndToEnd:
    """Tests end-to-end avec vraies données"""
    
    @pytest.fixture
    def pipeline(self):
        """Fixture pipeline avec données réelles"""
        return NBA19AggregationPipeline()
    
    def test_full_pipeline_execution(self, pipeline):
        """Exécuter pipeline complet si données disponibles"""
        # Vérifier si données existent
        if not pipeline.players_path.exists():
            pytest.skip("Données joueurs non disponibles")
        
        if not pipeline.games_path.exists():
            pytest.skip("Données matchs non disponibles")
        
        # Exécuter pipeline
        stats = pipeline.run()
        
        # Vérifications
        assert stats['errors'] == 0
        assert stats['team_season_records'] > 0
        assert stats['player_team_records'] > 0
    
    def test_output_files_created(self, pipeline):
        """Vérifier fichiers de sortie créés"""
        # Skip si pas de données
        if not pipeline.players_path.exists():
            pytest.skip("Données non disponibles")
        
        # Exécuter
        pipeline.run()
        
        # Vérifier fichiers
        team_output = pipeline.output_base / "team_season_stats"
        player_output = pipeline.output_base / "player_team_season"
        
        assert (team_output / "team_season_stats.json").exists()
        assert (player_output / "player_team_season.json").exists()
        assert (pipeline.output_base / "nba19_report.json").exists()


class TestNBA19DataQuality:
    """Tests qualité des données"""
    
    def test_no_duplicate_records(self):
        """Vérifier pas de doublons"""
        pipeline = NBA19AggregationPipeline()
        
        # Simuler avec doublons
        pipeline._cache['games'] = [
            {
                'game_id': '001',
                'season': '2023-24',
                'home_team_id': 1,
                'home_team_name': 'Lakers',
                'away_team_id': 2,
                'away_team_name': 'Celtics',
                'home_score': 110,
                'away_score': 105,
                'winner': 'home',
                'home_reb': 45,
                'home_ast': 25,
                'home_fg_pct': 0.48,
                'away_reb': 40,
                'away_ast': 20,
                'away_fg_pct': 0.45
            },
            {
                'game_id': '001',  # Doublon
                'season': '2023-24',
                'home_team_id': 1,
                'home_team_name': 'Lakers',
                'away_team_id': 2,
                'away_team_name': 'Celtics',
                'home_score': 110,
                'away_score': 105,
                'winner': 'home',
                'home_reb': 45,
                'home_ast': 25,
                'home_fg_pct': 0.48,
                'away_reb': 40,
                'away_ast': 20,
                'away_fg_pct': 0.45
            }
        ]
        
        df = pipeline._transform_team_stats()
        
        # Vérifier pas de doublons (team_id + season)
        if not df.empty:
            duplicates = df.duplicated(subset=['team_id', 'season']).sum()
            assert duplicates == 0, f"{duplicates} doublons trouvés"
    
    def test_coherent_statistics(self):
        """Vérifier cohérence statistique"""
        pipeline = NBA19AggregationPipeline()
        
        # Simuler données
        pipeline._cache['games'] = [
            {
                'game_id': '001',
                'season': '2023-24',
                'home_team_id': 1,
                'home_team_name': 'Lakers',
                'away_team_id': 2,
                'away_team_name': 'Celtics',
                'home_score': 110,
                'away_score': 105,
                'winner': 'home',
                'home_reb': 45,
                'home_ast': 25,
                'home_fg_pct': 0.48,
                'away_reb': 40,
                'away_ast': 20,
                'away_fg_pct': 0.45
            }
            for _ in range(10)  # 10 matchs identiques pour test
        ]
        
        df = pipeline._transform_team_stats()
        
        if not df.empty:
            # Vérifier win_pct entre 0 et 100
            assert df['win_pct'].between(0, 100).all()
            
            # Vérifier games_played > 0
            assert (df['games_played'] > 0).all()
            
            # Vérifier points positifs
            assert (df['avg_pts_scored'] > 0).all()


if __name__ == "__main__":
    # Exécution manuelle
    print("=" * 70)
    print("TESTS NBA-19 - Exécution manuelle")
    print("=" * 70)
    
    # Test simple
    pipeline = NBA19AggregationPipeline()
    
    print("\n1. Test d'initialisation...")
    assert pipeline is not None
    print("   ✓ Pipeline initialisé")
    
    print("\n2. Test extraction...")
    try:
        pipeline._extract()
        print(f"   ✓ Joueurs: {pipeline.stats['players_loaded']}")
        print(f"   ✓ Matchs: {pipeline.stats['games_loaded']}")
        print(f"   ✓ Équipes: {pipeline.stats['teams_loaded']}")
    except Exception as e:
        print(f"   ⚠ Erreur extraction: {e}")
    
    print("\n3. Test transformation...")
    try:
        if pipeline._cache.get('games'):
            team_df = pipeline._transform_team_stats()
            print(f"   ✓ Team-Season: {len(team_df)} records")
    except Exception as e:
        print(f"   ⚠ Erreur transformation: {e}")
    
    print("\n" + "=" * 70)
    print("Tests terminés")
    print("=" * 70)
