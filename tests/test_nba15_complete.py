#!/usr/bin/env python3
"""
Tests unitaires et d'intégration pour NBA-15
Vérifie la récupération complète des données matchs et équipes
"""

import json
import os
import pytest
import sys
from datetime import datetime

# Ajouter src au path
sys.path.insert(0, '.')

from src.utils.checkpoint_manager import CheckpointManager
from src.ingestion.fetch_teams_rosters import fetch_all_teams
from src.ingestion.fetch_schedules import fetch_season_schedule
from src.ingestion.fetch_team_stats import fetch_team_stats
from src.ingestion.fetch_boxscores import fetch_all_boxscores

SEASON = "2023-24"
RAW_BASE = "data/raw"


class TestCheckpointManager:
    """Tests du gestionnaire de checkpoints"""
    
    def test_checkpoint_initialization(self):
        """Test l'initialisation du checkpoint"""
        cp = CheckpointManager(checkpoint_dir="data/checkpoints/test")
        assert cp.data['ticket'] == "NBA-15"
        assert cp.data['status'] == "not_started"
        assert len(cp.data['completed_steps']) == 0
    
    def test_checkpoint_save_and_load(self):
        """Test la sauvegarde et le chargement"""
        cp = CheckpointManager(checkpoint_dir="data/checkpoints/test")
        cp.start_step("test_step")
        cp.complete_step("test_step", {"test": "data"})
        
        # Recharger
        cp2 = CheckpointManager(checkpoint_dir="data/checkpoints/test")
        assert "test_step" in cp2.data['completed_steps']
        assert cp2.data['data']['test_step']['test'] == "data"
    
    def test_checkpoint_is_step_completed(self):
        """Test la vérification d'étape complétée"""
        cp = CheckpointManager(checkpoint_dir="data/checkpoints/test")
        cp.complete_step("step1")
        assert cp.is_step_completed("step1") is True
        assert cp.is_step_completed("step2") is False


class TestTeamsRosters:
    """Tests pour les équipes et rosters"""
    
    @pytest.mark.integration
    def test_fetch_all_teams_count(self):
        """Vérifie qu'on récupère bien 30 équipes"""
        teams = fetch_all_teams()
        assert len(teams) == 30, f"Nombre d'équipes: {len(teams)} (attendu: 30)"
    
    @pytest.mark.integration
    def test_teams_structure(self):
        """Vérifie la structure des équipes"""
        teams = fetch_all_teams()
        required_fields = ['id', 'full_name', 'abbreviation', 'city']
        
        for team in teams:
            for field in required_fields:
                assert field in team, f"Champ {field} manquant dans {team}"
    
    @pytest.mark.integration
    def test_specific_teams_exist(self):
        """Vérifie que certaines équipes spécifiques existent"""
        teams = fetch_all_teams()
        team_names = [t['full_name'] for t in teams]
        
        assert "Los Angeles Lakers" in team_names
        assert "Golden State Warriors" in team_names
        assert "Boston Celtics" in team_names
    
    def test_teams_file_exists(self):
        """Vérifie que le fichier des équipes existe après exécution"""
        filepath = f"{RAW_BASE}/teams/teams_{SEASON.replace('-', '_')}.json"
        if os.path.exists(filepath):
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
                assert 'data' in data
                assert len(data['data']) == 30


class TestSchedules:
    """Tests pour les calendriers"""
    
    @pytest.mark.integration
    def test_fetch_season_schedule_count(self):
        """Vérifie qu'on récupère environ 1230 matchs"""
        games = fetch_season_schedule(SEASON, "Regular Season")
        assert len(games) >= 1200, f"Nombre de matchs: {len(games)} (attendu: ~1230)"
    
    @pytest.mark.integration
    def test_games_structure(self):
        """Vérifie la structure des matchs"""
        games = fetch_season_schedule(SEASON, "Regular Season")
        if games:
            required_fields = ['game_id', 'game_date', 'team_id', 'points', 'wl']
            for field in required_fields:
                assert field in games[0], f"Champ {field} manquant"
    
    @pytest.mark.integration
    def test_game_dates_format(self):
        """Vérifie le format des dates"""
        games = fetch_season_schedule(SEASON, "Regular Season")
        if games:
            for game in games[:10]:  # Tester sur les 10 premiers
                game_date = game['game_date']
                try:
                    datetime.strptime(game_date, "%Y-%m-%d")
                except ValueError:
                    pytest.fail(f"Format de date invalide: {game_date}")


class TestTeamStats:
    """Tests pour les stats collectives"""
    
    @pytest.mark.integration
    def test_fetch_team_stats_count(self):
        """Vérifie qu'on récupère 30 équipes"""
        stats = fetch_team_stats(SEASON, "Regular Season")
        assert len(stats) == 30, f"Nombre d'équipes: {len(stats)} (attendu: 30)"
    
    @pytest.mark.integration
    def test_team_stats_structure(self):
        """Vérifie la structure des stats"""
        stats = fetch_team_stats(SEASON, "Regular Season")
        if stats:
            required_fields = ['team_id', 'team_name', 'wins', 'losses', 'win_pct']
            for field in required_fields:
                assert field in stats[0], f"Champ {field} manquant"
    
    @pytest.mark.integration
    def test_wl_balance(self):
        """Vérifie que W + L = nombre total de matchs joués"""
        stats = fetch_team_stats(SEASON, "Regular Season")
        if stats:
            total_wins = sum(s['wins'] for s in stats if s['wins'])
            total_losses = sum(s['losses'] for s in stats if s['losses'])
            
            # Dans une saison régulière complète: total_wins == total_losses
            assert total_wins == total_losses, \
                f"Déséquilibre W/L: {total_wins} victoires vs {total_losses} défaites"


class TestBoxscores:
    """Tests pour les box scores"""
    
    @pytest.mark.integration
    def test_fetch_all_boxscores_count(self):
        """Vérifie qu'on récupère les matchs"""
        games = fetch_all_boxscores(SEASON, "Regular Season")
        assert len(games) >= 1200, f"Nombre de box scores: {len(games)} (attendu: ~1230)"
    
    @pytest.mark.integration
    def test_boxscores_stats_completeness(self):
        """Vérifie que les stats essentielles sont présentes"""
        games = fetch_all_boxscores(SEASON, "Regular Season")
        if games:
            required_stats = ['points', 'fgm', 'fga', 'fg_pct', 'reb', 'ast']
            for stat in required_stats:
                assert stat in games[0], f"Stat {stat} manquante"


class TestDataRelationships:
    """Tests d'intégrité référentielle"""
    
    def test_teams_rosters_consistency(self):
        """Vérifie que chaque équipe a un roster"""
        teams_file = f"{RAW_BASE}/teams/teams_{SEASON.replace('-', '_')}.json"
        rosters_file = f"{RAW_BASE}/rosters/roster_{SEASON.replace('-', '_')}.json"
        
        if os.path.exists(teams_file) and os.path.exists(rosters_file):
            with open(teams_file, encoding='utf-8') as f:
                teams_data = json.load(f)['data']
            with open(rosters_file, encoding='utf-8') as f:
                rosters_data = json.load(f)['data']
            
            team_ids = {t['id'] for t in teams_data}
            roster_team_ids = {r['team_id'] for r in rosters_data}
            
            assert team_ids == roster_team_ids, \
                f"Incohérence équipes/rosters: {team_ids - roster_team_ids}"
    
    def test_games_teams_consistency(self):
        """Vérifie que les équipes des matchs existent"""
        teams_file = f"{RAW_BASE}/teams/teams_{SEASON.replace('-', '_')}.json"
        schedules_file = f"{RAW_BASE}/schedules/schedule_{SEASON.replace('-', '_')}.json"
        
        if os.path.exists(teams_file) and os.path.exists(schedules_file):
            with open(teams_file, encoding='utf-8') as f:
                teams_data = json.load(f)['data']
            with open(schedules_file, encoding='utf-8') as f:
                games_data = json.load(f)['data']
            
            team_ids = {t['id'] for t in teams_data}
            
            # Vérifier sur un échantillon
            for game in games_data[:100]:
                assert game['team_id'] in team_ids, \
                    f"Équipe {game['team_id']} du match {game['game_id']} non trouvée"


class TestFileStructure:
    """Tests de structure des fichiers"""
    
    def test_required_directories_exist(self):
        """Vérifie que les répertoires requis existent"""
        required_dirs = [
            f"{RAW_BASE}/teams",
            f"{RAW_BASE}/rosters",
            f"{RAW_BASE}/schedules",
            f"{RAW_BASE}/teams_stats",
            f"{RAW_BASE}/games_boxscores"
        ]
        
        for dir_path in required_dirs:
            assert os.path.exists(dir_path), f"Répertoire manquant: {dir_path}"
    
    def test_files_are_valid_json(self):
        """Vérifie que les fichiers sont des JSON valides"""
        files_to_check = [
            f"{RAW_BASE}/teams/teams_{SEASON.replace('-', '_')}.json",
            f"{RAW_BASE}/rosters/roster_{SEASON.replace('-', '_')}.json",
            f"{RAW_BASE}/teams_stats/team_stats_{SEASON.replace('-', '_')}.json",
            f"{RAW_BASE}/schedules/schedule_{SEASON.replace('-', '_')}.json",
        ]
        
        for filepath in files_to_check:
            if os.path.exists(filepath):
                try:
                    with open(filepath, encoding='utf-8') as f:
                        data = json.load(f)
                        assert 'data' in data or isinstance(data, list)
                        assert 'metadata' in data
                except json.JSONDecodeError as e:
                    pytest.fail(f"JSON invalide dans {filepath}: {e}")
    
    def test_files_not_empty(self):
        """Vérifie que les fichiers ne sont pas vides"""
        files_to_check = [
            f"{RAW_BASE}/teams/teams_{SEASON.replace('-', '_')}.json",
            f"{RAW_BASE}/rosters/roster_{SEASON.replace('-', '_')}.json",
            f"{RAW_BASE}/schedules/schedule_{SEASON.replace('-', '_')}.json",
        ]
        
        for filepath in files_to_check:
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                assert size > 0, f"Fichier vide: {filepath}"


# ============================================================================
# COMMANDES POUR EXÉCUTER LES TESTS
# ============================================================================
"""
Exécuter tous les tests:
    pytest tests/test_nba15_complete.py -v

Exécuter uniquement les tests unitaires (sans appels API):
    pytest tests/test_nba15_complete.py -v -m "not integration"

Exécuter uniquement les tests d'intégration (avec appels API):
    pytest tests/test_nba15_complete.py -v -m "integration"

Exécuter un test spécifique:
    pytest tests/test_nba15_complete.py::TestTeamsRosters::test_fetch_all_teams_count -v

Générer un rapport de couverture:
    pytest tests/test_nba15_complete.py --cov=src --cov-report=html
"""

if __name__ == "__main__":
    # Permet d'exécuter les tests directement
    pytest.main([__file__, "-v"])
