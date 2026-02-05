#!/usr/bin/env python3
"""
Module d'ingestion des données NBA via nba-api
Récupère les données joueurs, équipes et matchs depuis NBA.com
Package: pip install nba-api
"""
# ============================================================================
# PARTIE 1 : IMPORTS
# ============================================================================
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
# Imports nba-api
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    playercareerstats,
    teamgamelog,
    commonplayerinfo,
    leaguegamefinder
)
from nba_api.live.nba.endpoints import scoreboard
# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# ============================================================================
# PARTIE 2 : CONSTANTES
# ============================================================================
RAW_DATA_PATH = "data/raw"
# ============================================================================
# PARTIE 3 : FONCTIONS UTILITAIRES
# ============================================================================
def ensure_directory(path: str):
    """Crée un répertoire s'il n'existe pas"""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"📁 Répertoire créé: {path}")
def save_to_json(data: Any, filename: str):
    """Sauvegarde les données avec métadonnées"""
    ensure_directory(RAW_DATA_PATH)
    
    filepath = os.path.join(RAW_DATA_PATH, filename)
    
    output = {
        "data": data,
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "record_count": len(data) if isinstance(data, list) else 1,
            "source": "nba-api (NBA.com)",
            "package_version": "1.1.11"
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(filepath)
    logger.info(f"💾 Fichier sauvegardé: {filepath} ({file_size:,} octets)")
# ============================================================================
# PARTIE 4 : RÉCUPÉRATION DONNÉES STATIQUES
# ============================================================================
def fetch_all_players():
    """
    Récupère tous les joueurs NBA (actifs et historiques)
    Retourne ~4000+ joueurs avec leurs infos de base
    """
    logger.info("🏀 Récupération de tous les joueurs NBA...")
    
    # Récupère tous les joueurs (actifs + historique)
    all_players = players.get_players()
    
    logger.info(f"✅ {len(all_players)} joueurs récupérés")
    return all_players
def fetch_active_players():
    """
    Récupère uniquement les joueurs actifs (~500 joueurs)
    """
    logger.info("🏀 Récupération des joueurs actifs...")
    
    active_players = players.get_active_players()
    
    logger.info(f"✅ {len(active_players)} joueurs actifs récupérés")
    return active_players
def fetch_all_teams():
    """
    Récupère toutes les équipes NBA (30 équipes)
    """
    logger.info("🏀 Récupération des équipes NBA...")
    
    all_teams = teams.get_teams()
    
    logger.info(f"✅ {len(all_teams)} équipes récupérées")
    return all_teams
# ============================================================================
# PARTIE 5 : RÉCUPÉRATION STATISTIQUES DÉTAILLÉES
# ============================================================================
def fetch_player_career_stats(player_id: int, player_name: str = ""):
    """
    Récupère les statistiques de carrière d'un joueur
    
    Args:
        player_id: ID du joueur (ex: 2544 pour LeBron James)
        player_name: Nom pour le logging (optionnel)
    """
    logger.info(f"📊 Stats carrière pour {player_name or player_id}...")
    
    try:
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        career_data = career.get_dict()
        
        return career_data
        
    except Exception as e:
        logger.error(f"❌ Erreur stats carrière: {e}")
        return None
def fetch_player_info(player_id: int):
    """
    Récupère les informations détaillées d'un joueur
    """
    logger.info(f"ℹ️  Infos joueur {player_id}...")
    
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        info_data = info.get_dict()
        
        return info_data
        
    except Exception as e:
        logger.error(f"❌ Erreur infos joueur: {e}")
        return None
def fetch_team_games(team_id: int, season: str = "2023-24"):
    """
    Récupère les matchs d'une équipe pour une saison
    
    Args:
        team_id: ID de l'équipe
        season: Saison (format: 2023-24)
    """
    logger.info(f"🎮 Matchs équipe {team_id} (saison {season})...")
    
    try:
        games = teamgamelog.TeamGameLog(
            team_id=team_id,
            season=season
        )
        games_data = games.get_dict()
        
        return games_data
        
    except Exception as e:
        logger.error(f"❌ Erreur matchs équipe: {e}")
        return None
def fetch_league_games(season: str = "2023-24", season_type: str = "Regular Season"):
    """
    Récupère tous les matchs de la ligue pour une saison
    
    Args:
        season: Saison (ex: 2023-24)
        season_type: Type de saison (Regular Season, Playoffs, etc.)
    """
    logger.info(f"🎮 Tous les matchs NBA {season} ({season_type})...")
    
    try:
        games = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            season_type_nullable=season_type
        )
        games_data = games.get_dict()
        
        return games_data
        
    except Exception as e:
        logger.error(f"❌ Erreur matchs ligue: {e}")
        return None
def fetch_live_scoreboard():
    """
    Récupère le scoreboard des matchs en cours (temps réel)
    """
    logger.info("🔴 Récupération des matchs en cours...")
    
    try:
        live = scoreboard.ScoreBoard()
        live_data = live.get_dict()
        
        return live_data
        
    except Exception as e:
        logger.error(f"❌ Erreur live scoreboard: {e}")
        return None
# ============================================================================
# PARTIE 6 : FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Exécute l'ingestion complète des données NBA
    """
    logger.info("="*60)
    logger.info("🏀 DÉMARRAGE INGESTION NBA - nba-api")
    logger.info("="*60)
    
    try:
        # ---------------------------------------------------------------------
        # ÉTAPE 1 : Données statiques (joueurs et équipes)
        # ---------------------------------------------------------------------
        logger.info("\n📦 ÉTAPE 1: Données statiques")
        
        # Tous les joueurs
        all_players = fetch_all_players()
        save_to_json(all_players, "all_players.json")
        
        # Joueurs actifs uniquement
        active_players = fetch_active_players()
        save_to_json(active_players, "active_players.json")
        
        # Équipes
        all_teams = fetch_all_teams()
        save_to_json(all_teams, "teams.json")
        
        # ---------------------------------------------------------------------
        # ÉTAPE 2 : Stats détaillées (exemple avec top joueurs)
        # ---------------------------------------------------------------------
        logger.info("\n📊 ÉTAPE 2: Statistiques détaillées (exemples)")
        
        # Exemple: Stats de LeBron James (ID: 2544)
        lebron_stats = fetch_player_career_stats(2544, "LeBron James")
        if lebron_stats:
            save_to_json(lebron_stats, "player_2544_lebron_career.json")
        
        # Exemple: Infos détaillées LeBron
        lebron_info = fetch_player_info(2544)
        if lebron_info:
            save_to_json(lebron_info, "player_2544_lebron_info.json")
        
        # ---------------------------------------------------------------------
        # ÉTAPE 3 : Matchs de la saison
        # ---------------------------------------------------------------------
        logger.info("\n🎮 ÉTAPE 3: Matchs NBA 2023-24")
        
        # Tous les matchs de la saison régulière
        season_games = fetch_league_games(season="2023-24")
        if season_games:
            save_to_json(season_games, "games_2023_24_regular.json")
        
        # ---------------------------------------------------------------------
        # ÉTAPE 4 : Données temps réel (si match en cours)
        # ---------------------------------------------------------------------
        logger.info("\n🔴 ÉTAPE 4: Matchs en cours (live)")
        
        live_games = fetch_live_scoreboard()
        if live_games:
            save_to_json(live_games, "live_scoreboard.json")
        
        # ---------------------------------------------------------------------
        # RÉSUMÉ
        # ---------------------------------------------------------------------
        logger.info("\n" + "="*60)
        logger.info("✅ INGESTION TERMINÉE AVEC SUCCÈS")
        logger.info("="*60)
        logger.info(f"📁 Fichiers créés dans: {RAW_DATA_PATH}/")
        logger.info(f"   • all_players.json ({len(all_players)} joueurs)")
        logger.info(f"   • active_players.json ({len(active_players)} joueurs actifs)")
        logger.info(f"   • teams.json ({len(all_teams)} équipes)")
        logger.info("="*60)
        
    except Exception as e:
        logger.error("\n" + "="*60)
        logger.error("❌ ERREUR FATALE")
        logger.error("="*60)
        logger.error(f"Détails: {str(e)}")
        logger.error("\nConseils:")
        logger.error("1. Vérifie ta connexion internet")
        logger.error("2. Réessaie dans quelques minutes (rate limit NBA.com)")
        logger.error("3. Vérifie que nba-api est installé: pip install nba-api")
        logger.error("="*60)
        raise
# ============================================================================
# PARTIE 7 : POINT D'ENTRÉE
# ============================================================================
if __name__ == "__main__":
    main()

