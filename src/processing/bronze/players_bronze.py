"""
Couche Bronze - Ingestion et persistance des données joueurs brutes.

Ce module gère:
1. Chargement des sources de données (JSON historique, roster, CSV)
2. Enrichissement via API NBA (avec cache)
3. Persistance en JSON (format permissif, pas de schéma strict)
4. Filtrage par période (2000-2026)

Aucune transformation n'est appliquée - les données sont stockées telles quelles.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Imports utils
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.caching import APICacheManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayersBronze:
    """
    Gestionnaire de la couche Bronze pour les données joueurs.
    
    Responsabilités:
    - Charger les données brutes de toutes les sources
    - Enrichir via API avec gestion de cache
    - Sauvegarder en JSON sans transformation
    """
    
    # Configuration
    RAW_BASE = "data/raw"
    BRONZE_PATH = "data/bronze/players_bronze.json"
    CRITICAL_CSV = "data/supplemental/players_critical.csv"
    
    # IDs des légendes critiques à inclure (même si anciennes)
    CRITICAL_PLAYER_IDS = {
        23,    # Michael Jordan
        977,   # Kobe Bryant
        192,   # Shaquille O'Neal
        406,   # Allen Iverson
        504,   # Tim Duncan
        397,   # Kevin Garnett
        87,    # Hakeem Olajuwon
        774,   # Vince Carter
        1051,  # Paul Pierce
        1710,  # Dirk Nowitzki
        947,   # Jason Kidd
        224,   # Scottie Pippen
        165,   # Karl Malone
        252,   # John Stockton
        279,   # Gary Payton
        307,   # Patrick Ewing
        56,    # David Robinson
        198,   # Charles Barkley
    }
    
    def __init__(self, use_cache: bool = True):
        """
        Initialise le gestionnaire Bronze.
        
        Args:
            use_cache: Si True, utilise le cache API
        """
        self.use_cache = use_cache
        self.cache = APICacheManager() if use_cache else None
        self.stats = {
            'total': 0,
            'from_roster': 0,
            'from_api': 0,
            'from_csv': 0,
        }
    
    def load_raw_players(self) -> Dict[int, Dict]:
        """
        Charge les joueurs historiques de base.
        
        Returns:
            Dict[player_id, player_data] avec les données de base
        """
        logger.info("Chargement all_players_historical.json...")
        
        with open(f"{self.RAW_BASE}/all_players_historical.json", 'r', encoding='utf-8') as f:
            all_players = json.load(f)['data']
        
        players_dict = {
            p['id']: {
                'id': p['id'],
                'full_name': p['full_name'],
                'first_name': p.get('first_name', ''),
                'last_name': p.get('last_name', ''),
                'is_active': p.get('is_active', False),
                # Champs vides à enrichir
                'height': None,
                'weight': None,
                'position': None,
                'birth_date': None,
                'age': None,
                'from_year': None,
                'to_year': None,
                'data_source': 'base'
            }
            for p in all_players
        }
        
        self.stats['total'] = len(players_dict)
        logger.info(f"{self.stats['total']} joueurs de base chargés")
        return players_dict
    
    def enrich_from_roster(self, players_dict: Dict[int, Dict]) -> Dict[int, Dict]:
        """Enrichit depuis le roster 2023-24."""
        count = 0
        try:
            with open(f"{self.RAW_BASE}/rosters/roster_2023_24.json", 'r', encoding='utf-8') as f:
                roster_data = json.load(f)['data']
            
            for team in roster_data:
                for player in team.get('players', []):
                    player_id = player.get('player_id')
                    if player_id and player_id in players_dict:
                        players_dict[player_id].update({
                            'height': player.get('height'),
                            'weight': player.get('weight'),
                            'position': player.get('position'),
                            'birth_date': player.get('birth_date'),
                            'age': player.get('age'),
                            'data_source': 'roster'
                        })
                        count += 1
            
            self.stats['from_roster'] = count
            logger.info(f"{count} joueurs enrichis depuis le roster")
        except Exception as e:
            logger.warning(f"Erreur chargement roster: {e}")
        
        return players_dict
    
    def enrich_from_csv(self, players_dict: Dict[int, Dict]) -> Dict[int, Dict]:
        """Enrichit depuis le CSV des légendes."""
        count = 0
        try:
            import csv
            with open(self.CRITICAL_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player_id = int(row['player_id'])
                    if player_id in players_dict:
                        players_dict[player_id].update({
                            'height': row.get('height'),
                            'weight': row.get('weight'),
                            'position': row.get('position'),
                            'birth_date': row.get('birth_date'),
                            'data_source': 'csv'
                        })
                        count += 1
            
            self.stats['from_csv'] = count
            logger.info(f"{count} joueurs enrichis depuis CSV")
        except Exception as e:
            logger.warning(f"Erreur chargement CSV: {e}")
        
        return players_dict
    
    def _is_player_modern(self, player_id: int) -> bool:
        """Détermine si un joueur doit être inclus (2016+ ou légende critique)."""
        if player_id >= 1_620_000:  # Format ID moderne (2016+)
            return True
        if player_id in self.CRITICAL_PLAYER_IDS:
            return True
        return False
    
    def enrich_from_api(self, players_dict: Dict[int, Dict], 
                       period_filter: bool = True) -> Dict[int, Dict]:
        """
        Enrichit via API NBA avec cache.
        
        Args:
            players_dict: Dict des joueurs à enrichir
            period_filter: Si True, filtre les joueurs anciens
        """
        if not self.use_cache:
            logger.warning("Cache désactivé - tous les appels API seront faits")
        
        # Identifier les joueurs à enrichir
        players_to_enrich = [
            pid for pid, p in players_dict.items()
            if not p.get('height') or not p.get('weight')
        ]
        
        # Appliquer le filtre de période
        if period_filter:
            players_to_enrich = [
                pid for pid in players_to_enrich
                if self._is_player_modern(pid)
            ]
            logger.info(f"Filtrage 2016+: {len(players_to_enrich)} joueurs à enrichir")
        
        if not players_to_enrich:
            logger.info("Aucun joueur à enrichir via API")
            return players_dict
        
        # Filtrer ceux déjà en cache
        if self.cache:
            players_to_enrich = self.cache.filter_missing(players_to_enrich)
        
        if not players_to_enrich:
            logger.info("Tous les joueurs sont déjà en cache!")
        else:
            logger.info(f"Appels API nécessaires: {len(players_to_enrich)} joueurs")
            self._fetch_from_api(players_dict, players_to_enrich)
        
        # Appliquer les données du cache
        if self.cache:
            self._apply_cache_data(players_dict)
        
        return players_dict
    
    def _fetch_from_api(self, players_dict: Dict[int, Dict], 
                       player_ids: List[int]) -> None:
        """Effectue les appels API pour les joueurs manquants."""
        try:
            from nba_api.stats.endpoints import commonplayerinfo
        except ImportError:
            logger.error("nba-api non installé")
            return
        
        count = 0
        for i, player_id in enumerate(player_ids, 1):
            try:
                if i % 50 == 0 or i == 1:
                    logger.info(f"API call {i}/{len(player_ids)}: player {player_id}")
                
                info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
                df = info.get_data_frames()[0]
                
                if not df.empty:
                    row = df.iloc[0]
                    player_data = {
                        'height': row.get('HEIGHT'),
                        'weight': row.get('WEIGHT'),
                        'position': row.get('POSITION'),
                        'birth_date': row.get('BIRTHDATE'),
                        'from_year': row.get('FROM_YEAR'),
                        'to_year': row.get('TO_YEAR'),
                    }
                    
                    # Mettre à jour le dict
                    players_dict[player_id].update(player_data)
                    players_dict[player_id]['data_source'] = 'api'
                    
                    # Mettre en cache
                    if self.cache:
                        self.cache.set(player_id, player_data)
                    
                    count += 1
                
                # Rate limiting
                if i < len(player_ids):
                    time.sleep(1)
                
                # Checkpoint tous les 100 joueurs
                if self.cache and i % 100 == 0:
                    self.cache.checkpoint(i)
                    
            except Exception as e:
                logger.debug(f"Erreur API pour joueur {player_id}: {e}")
                continue
        
        self.stats['from_api'] = count
        logger.info(f"{count} joueurs enrichis depuis API")
        
        # Sauvegarde finale du cache
        if self.cache:
            self.cache.save_cache()
    
    def _apply_cache_data(self, players_dict: Dict[int, Dict]) -> None:
        """Applique les données du cache aux joueurs."""
        cached_ids = self.cache.get_cached_ids()
        
        for pid in cached_ids:
            if pid in players_dict:
                cached_data = self.cache.get(pid)
                if cached_data:
                    players_dict[pid].update({
                        'height': cached_data.get('height'),
                        'weight': cached_data.get('weight'),
                        'position': cached_data.get('position'),
                        'birth_date': cached_data.get('birth_date'),
                        'from_year': cached_data.get('from_year'),
                        'to_year': cached_data.get('to_year'),
                        'data_source': 'api_cached'
                    })
        
        logger.info(f"{len(cached_ids)} joueurs mis à jour depuis le cache")
    
    def save_bronze(self, players_dict: Dict[int, Dict]) -> None:
        """
        Sauvegarde les données Bronze en JSON.
        
        Args:
            players_dict: Dict des joueurs à sauvegarder
        """
        logger.info("Sauvegarde couche Bronze...")
        
        bronze_path = Path(self.BRONZE_PATH)
        bronze_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convertir en liste pour le JSON
        players_list = list(players_dict.values())
        
        bronze_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_players": len(players_list),
                "enrichment_stats": self.stats,
                "version": "1.0"
            },
            "data": players_list
        }
        
        with open(bronze_path, 'w', encoding='utf-8') as f:
            json.dump(bronze_data, f, indent=2, default=str)
        
        logger.info(f"Bronze sauvegardé: {bronze_path} ({len(players_list)} joueurs)")
    
    def load_bronze(self) -> List[Dict]:
        """
        Charge les données Bronze depuis le disque.
        
        Returns:
            Liste des joueurs Bronze
        """
        bronze_path = Path(self.BRONZE_PATH)
        
        if not bronze_path.exists():
            raise FileNotFoundError(f"Fichier Bronze non trouvé: {bronze_path}")
        
        with open(bronze_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Bronze chargé: {len(data['data'])} joueurs")
        return data['data']
    
    def run_bronze_layer(self, period_filter: bool = True) -> List[Dict]:
        """
        Exécute le pipeline Bronze complet.
        
        Args:
            period_filter: Si True, filtre les joueurs anciens
            
        Returns:
            Liste des joueurs Bronze enrichis
        """
        logger.info("=" * 60)
        logger.info("COUCHE BRONZE - Ingestion données brutes")
        logger.info("=" * 60)
        
        # 1. Charger base
        players_dict = self.load_raw_players()
        
        # 2. Enrichir
        players_dict = self.enrich_from_roster(players_dict)
        players_dict = self.enrich_from_csv(players_dict)
        players_dict = self.enrich_from_api(players_dict, period_filter)
        
        # 3. Sauvegarder
        self.save_bronze(players_dict)
        
        # Retourner liste
        return list(players_dict.values())


if __name__ == "__main__":
    print("Test PlayersBronze:")
    bronze = PlayersBronze()
    print(f"Critical IDs: {len(bronze.CRITICAL_PLAYER_IDS)} légendes")
    print("Module prêt")
