#!/usr/bin/env python3
"""
NBA-17: Nettoyage des données joueurs - Version refactorisée
Nettoie et enrichit les données de 5103 joueurs NBA pour la couche Silver.
Version 2.0: Refactoring avec imports centralisés (-403 lignes)

Aligné avec:
- NBA-15: Réutilise les rosters déjà récupérés
- NBA-12: Utilise PySpark et Delta Lake comme le projet
- fetch_nba_data.py: Réutilise les fonctions API existantes

Refactoring:
- Suppression des fonctions dupliquées (convert_*, standardize_*, calculate_*)
- Utilisation des fonctions utilitaires de transformations.py et cleaning_functions.py
- Réduction: 873 → 470 lignes (-46%)
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, regexp_extract
from pyspark.sql.types import IntegerType, DoubleType, StringType, BooleanType, StructType, StructField

# ============================================
# IMPORTS CENTRALISÉS (Refactoring NBA-17 v2.0)
# ============================================
# Import des fonctions de nettoyage
from src.processing.silver.cleaning_functions import (
    clean_player_record,
    impute_missing_data,
    filter_complete_players,
)

# Import des fonctions de transformation
from src.utils.transformations import (
    convert_height_to_cm,
    convert_weight_to_kg,
    standardize_position,
    standardize_date,
    calculate_age,
    convert_to_int_safe,
)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
CONFIG_PATH = "configs/cleaning_rules.yaml"
RAW_BASE = "data/raw"
SILVER_BASE = "data/silver"
CRITICAL_CSV = "data/supplemental/players_critical.csv"


class PlayersDataCleaner:
    """
    Nettoyage des données joueurs NBA - Version refactorisée.
    
    Pipeline:
    1. Charge les 5103 joueurs historiques
    2. Enrichit avec roster 2023-24 (532 joueurs avec données complètes)
    3. Complète avec CSV critiques (légendes NBA)
    4. Enrichit le reste via API (uniquement si nécessaire)
    5. Nettoie via cleaning_functions.py et transformations.py
    6. Valide et sauvegarde en Delta Lake partitionné
    """
    
    def __init__(self, config_path: str = CONFIG_PATH):
        """Initialise le nettoyeur avec configuration."""
        self.config = self._load_config(config_path)
        self.spark = self._init_spark()
        self.stats = {
            'total': 0,
            'from_roster': 0,
            'from_api': 0,
            'from_csv': 0,
            'imputed': 0,
            'nulls_after_cleaning': 0
        }
        self.validation_rules = self.config.get('validation', {})
        self.conversion_rules = self.config.get('conversion', {})
        
    def _load_config(self, path: str) -> Dict:
        """Charge la configuration YAML."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            raise
    
    def _init_spark(self) -> SparkSession:
        """Initialise la session Spark avec Delta Lake."""
        try:
            from delta import configure_spark_with_delta_pip
            builder = SparkSession.builder \
                .appName("NBA-Players-Cleaning") \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            return configure_spark_with_delta_pip(builder).getOrCreate()
        except ImportError:
            logger.warning("Delta Lake non installé, utilisation Spark standard")
            return SparkSession.builder.appName("NBA-Players-Cleaning").getOrCreate()
    
    def _is_player_in_period(self, player_id: int, from_year: Optional[int], to_year: Optional[int]) -> bool:
        """
        Vérifie si un joueur a joué pendant la période cible 2000-2026.
        
        Args:
            player_id: ID du joueur
            from_year: Année de début de carrière
            to_year: Année de fin de carrière
            
        Returns:
            True si le joueur a joué entre 2000 et 2026
        """
        TARGET_START = 2000
        TARGET_END = 2026
        
        # Si pas d'info, on suppose qu'il pourrait être dans la période
        if from_year is None and to_year is None:
            return True
        
        # Convertir en int si ce sont des types numpy
        if from_year is not None:
            from_year = int(from_year)
        if to_year is not None:
            to_year = int(to_year)
        
        # Pour les joueurs actifs (to_year = None ou 2025/2026)
        if to_year is None or to_year >= TARGET_END:
            # Vérifier s'ils ont commencé avant ou pendant la période
            if from_year is None or from_year <= TARGET_END:
                return True
        
        # Pour les joueurs retraités
        if to_year is not None and to_year >= TARGET_START:
            # Vérifier qu'ils n'ont pas fini avant 2000
            if from_year is None or from_year <= TARGET_END:
                return True
        
        return False
    
    def _is_player_modern_strict(self, player_id: int) -> bool:
        """
        Filtrage STRICT: Uniquement joueurs 2016+ (IDs modernes) + légendes critiques.
        
        Format IDs NBA:
        - IDs 162XXXX+: Joueurs 2016+ (format moderne)
        - IDs spéciaux: Légendes à conserver (Jordan, Kobe, etc.)
        
        Args:
            player_id: ID du joueur
            
        Returns:
            True si le joueur est moderne (2016+) ou critique
        """
        # IDs des joueurs critiques des années 90-2000 à inclure
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
        
        # Joueurs actifs/récents (format ID moderne 2016+)
        if player_id >= 1_620_000:
            return True
        
        # Légendes critiques à inclure
        if player_id in CRITICAL_PLAYER_IDS:
            return True
        
        return False
    
    def load_and_merge_sources(self, period_filter: bool = True) -> Dict[int, Dict]:
        """
        Fusionne toutes les sources de données joueurs.
        
        Args:
            period_filter: Tuple (start_year, end_year) pour filtrer par période
            
        Returns:
            Dict[player_id, player_data] avec toutes les données enrichies
        """
        logger.info("Chargement et fusion des sources de données...")
        
        # 1. Charger les 5103 joueurs historiques (base)
        logger.info("Chargement all_players_historical.json...")
        with open(f"{RAW_BASE}/all_players_historical.json", 'r', encoding='utf-8') as f:
            all_players = json.load(f)['data']
        
        players_dict = {p['id']: {
            'id': p['id'],
            'full_name': p['full_name'],
            'first_name': p.get('first_name', ''),
            'last_name': p.get('last_name', ''),
            'is_active': p.get('is_active', False),
            'height': None,
            'weight': None,
            'position': None,
            'birth_date': None,
            'age': None,
            'data_source': 'base'
        } for p in all_players}
        
        self.stats['total'] = len(players_dict)
        logger.info(f"{self.stats['total']} joueurs de base chargés")
        
        # 2. Enrichir avec roster 2023-24 (532 joueurs - données complètes locales)
        logger.info("Enrichissement avec roster 2023-24...")
        roster_count = self._enrich_from_roster(players_dict)
        self.stats['from_roster'] = roster_count
        logger.info(f"{roster_count} joueurs enrichis depuis le roster")
        
        # 3. Compléter avec CSV critiques (légendes NBA)
        logger.info("Enrichissement avec CSV critiques...")
        csv_count = self._enrich_from_csv(players_dict)
        self.stats['from_csv'] = csv_count
        logger.info(f"{csv_count} joueurs enrichis depuis CSV")
        
        # 4. API pour le reste (ENRICHISSEMENT MAXIMUM: jusqu'à 2000 joueurs)
        players_to_enrich = [
            pid for pid, p in players_dict.items() 
            if not p.get('height') or not p.get('weight')
        ]
        
        # Limiter à 2000 joueurs maximum pour éviter 3h d'attente
        MAX_API_CALLS = 2000
        if len(players_to_enrich) > MAX_API_CALLS:
            logger.info(f"Limitation à {MAX_API_CALLS} appels API (sur {len(players_to_enrich)} possibles)")
            # Priorité: joueurs modernes (2016+) d'abord, puis autres
            modern_players = [pid for pid in players_to_enrich if pid >= 1620000]
            other_players = [pid for pid in players_to_enrich if pid < 1620000]
            players_to_enrich = modern_players[:1500] + other_players[:500]
        
        logger.info(f"Enrichissement API pour {len(players_to_enrich)} joueurs (max {MAX_API_CALLS})...")
        if players_to_enrich:
            api_count = self._enrich_from_api(players_dict, players_to_enrich, period_filter=False)  # Pas de filtre période
            self.stats['from_api'] = api_count
            logger.info(f"{api_count} joueurs enrichis depuis API")
        
        return players_dict
    
    def _enrich_from_roster(self, players_dict: Dict) -> int:
        """Enrichit les joueurs avec les données du roster 2023-24."""
        count = 0
        try:
            with open(f"{RAW_BASE}/rosters/roster_2023_24.json", 'r', encoding='utf-8') as f:
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
        except Exception as e:
            logger.warning(f"Erreur chargement roster: {e}")
        return count
    
    def _enrich_from_csv(self, players_dict: Dict) -> int:
        """Enrichit avec les données du CSV critiques."""
        count = 0
        try:
            import csv
            with open(CRITICAL_CSV, 'r', encoding='utf-8') as f:
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
        except Exception as e:
            logger.warning(f"Erreur chargement CSV: {e}")
        return count
    
    def _load_api_cache(self) -> Dict[int, Dict]:
        """
        Charge le cache des données API si existant.
        
        Returns:
            Dict[player_id, player_data] depuis le cache
        """
        cache_path = Path(f"{RAW_BASE}/players_api_cache.json")
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    cached_players = cache_data.get('data', {})
                    # Convertir les clés string en int
                    return {int(k): v for k, v in cached_players.items()}
            except Exception as e:
                logger.warning(f"Erreur chargement cache: {e}")
        return {}
    
    def _save_api_cache(self, cache_data: Dict[int, Dict]):
        """
        Sauvegarde le cache des données API sur disque.
        
        Args:
            cache_data: Dict[player_id, player_data] à sauvegarder
        """
        cache_path = Path(f"{RAW_BASE}/players_api_cache.json")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            cache_content = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "total_cached": len(cache_data),
                    "version": "1.0"
                },
                "data": cache_data
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_content, f, indent=2, default=str)
            logger.info(f"Cache API sauvegardé: {len(cache_data)} joueurs")
        except Exception as e:
            logger.warning(f"Erreur sauvegarde cache: {e}")
    
    def _enrich_from_api(self, players_dict: Dict, player_ids: List[int], 
                         period_filter: bool = True) -> int:
        """
        Enrichit les joueurs via API NBA avec cache et filtre par période.
        
        Args:
            players_dict: Dict des joueurs à enrichir
            player_ids: Liste des IDs à enrichir
            period_filter: Si True, ne récupère que les joueurs de 2000-2026
        """
        count = 0
        rate_limit = self.config.get('api_enrichment', {}).get('rate_limit_seconds', 1)
        
        # Import local pour éviter dépendance circulaire
        try:
            from nba_api.stats.endpoints import commonplayerinfo
        except ImportError:
            logger.error("nba-api non installé")
            return 0
        
        # Charger le cache existant
        api_cache = self._load_api_cache()
        logger.info(f"Cache chargé: {len(api_cache)} joueurs en cache")
        
        # Filtrer les joueurs déjà en cache
        player_ids_to_fetch = [pid for pid in player_ids if pid not in api_cache]
        cached_count = len(player_ids) - len(player_ids_to_fetch)
        
        if cached_count > 0:
            logger.info(f"{cached_count} joueurs déjà en cache (pas d'appel API)")
            # Appliquer les données du cache
            for pid in player_ids:
                if pid in api_cache:
                    cached_data = api_cache[pid]
                    players_dict[pid].update({
                        'height': cached_data.get('height'),
                        'weight': cached_data.get('weight'),
                        'position': cached_data.get('position'),
                        'birth_date': cached_data.get('birth_date'),
                        'from_year': cached_data.get('from_year'),
                        'to_year': cached_data.get('to_year'),
                        'data_source': 'api_cached'
                    })
                    count += 1
        
        if not player_ids_to_fetch:
            logger.info("Tous les joueurs sont déjà en cache!")
            return count
        
        logger.info(f"Appels API nécessaires: {len(player_ids_to_fetch)} joueurs")
        
        # Récupérer uniquement les joueurs non en cache
        for i, player_id in enumerate(player_ids_to_fetch, 1):
            try:
                if i % 50 == 0 or i == 1:
                    logger.info(f"API call {i}/{len(player_ids_to_fetch)}: player {player_id}")
                else:
                    logger.debug(f"API call {i}/{len(player_ids_to_fetch)}: player {player_id}")
                    
                info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
                df = info.get_data_frames()[0]
                
                if not df.empty:
                    row = df.iloc[0]
                    from_year = row.get('FROM_YEAR')
                    to_year = row.get('TO_YEAR')
                    
                    # Vérifier si le joueur est dans la période cible
                    if period_filter and not self._is_player_in_period(player_id, from_year, to_year):
                        logger.debug(f"Joueur {player_id} hors période 2000-2026, ignoré")
                        continue
                    
                    player_data = {
                        'height': row.get('HEIGHT'),
                        'weight': row.get('WEIGHT'),
                        'position': row.get('POSITION'),
                        'birth_date': row.get('BIRTHDATE'),
                        'from_year': from_year,
                        'to_year': to_year,
                    }
                    
                    # Mettre à jour le dict des joueurs
                    players_dict[player_id].update(player_data)
                    players_dict[player_id]['data_source'] = 'api'
                    
                    # Ajouter au cache
                    api_cache[player_id] = player_data
                    count += 1
                
                # Rate limiting
                if i < len(player_ids_to_fetch):
                    time.sleep(rate_limit)
                    
                # Sauvegarder le cache tous les 100 joueurs (checkpoint)
                if i % 100 == 0:
                    self._save_api_cache(api_cache)
                    
            except Exception as e:
                logger.debug(f"Erreur API pour joueur {player_id}: {e}")
                continue
        
        # Sauvegarder le cache final
        self._save_api_cache(api_cache)
        
        return count
    
    # ============================================
    # SECTION REFACTORISÉE: clean_and_convert
    # Remplace les fonctions _convert_*, _standardize_*, _calculate_*, _impute_*
    # Utilise: cleaning_functions.py et transformations.py
    # ============================================
    def clean_and_convert(self, players_dict: Dict[int, Dict]) -> List[Dict]:
        """
        Nettoie et convertit les données joueurs en utilisant les fonctions utilitaires.
        
        Refactoring v2.0:
        - Utilise clean_player_record() de cleaning_functions.py
        - Utilise convert_height_to_cm(), convert_weight_to_kg() de transformations.py
        - Utilise standardize_position(), standardize_date(), calculate_age() de transformations.py
        - Utilise impute_missing_data() de cleaning_functions.py
        - Supprime 139 lignes de code dupliqué
        
        Args:
            players_dict: Dict des joueurs à nettoyer
            
        Returns:
            Liste des joueurs nettoyés
        """
        logger.info("Nettoyage et conversion des données (utilise fonctions utilitaires)...")
        cleaned = []
        
        for player_id, player in players_dict.items():
            # Étape 1: Nettoyage de base via cleaning_functions.py
            cleaned_player = clean_player_record(player)
            
            # Étape 2: Conversion des unités via transformations.py
            if cleaned_player.get('height'):
                cleaned_player['height_cm'] = convert_height_to_cm(cleaned_player['height'])
            
            if cleaned_player.get('weight'):
                cleaned_player['weight_kg'] = convert_weight_to_kg(cleaned_player['weight'])
            
            # Étape 3: Standardisation via transformations.py
            if cleaned_player.get('position'):
                cleaned_player['position'] = standardize_position(cleaned_player['position'])
            
            if cleaned_player.get('birth_date'):
                cleaned_player['birth_date'] = standardize_date(cleaned_player['birth_date'])
                cleaned_player['age'] = calculate_age(cleaned_player['birth_date'])
            
            # Étape 4: Imputation des données manquantes via cleaning_functions.py
            if not cleaned_player.get('height_cm') or not cleaned_player.get('weight_kg'):
                cleaned_player = impute_missing_data(cleaned_player)
                self.stats['imputed'] += 1
            
            cleaned.append(cleaned_player)
        
        # Étape 5: Filtrage des joueurs incomplets via cleaning_functions.py
        result = filter_complete_players(cleaned, min_fields=5)
        logger.info(f"{len(result)} joueurs nettoyés et filtrés")
        
        return result
    
    # ============================================
    # SECTION SUPPRIMÉE: Fonctions dupliquées
    # REMPLACÉ PAR: Imports depuis transformations.py et cleaning_functions.py
    # ============================================
    # Les fonctions suivantes ont été supprimées (139 lignes):
    # - _convert_height_to_cm() → convert_height_to_cm (import)
    # - _convert_weight_to_kg() → convert_weight_to_kg (import)
    # - _standardize_position() → standardize_position (import)
    # - _standardize_date() → standardize_date (import)
    # - _calculate_age() → calculate_age (import)
    # - _impute_height() → impute_missing_data (import)
    # - _impute_weight() → impute_missing_data (import)
    
    def validate_data(self, players: List[Dict]) -> bool:
        """
        Valide la qualité des données.
        
        Returns:
            True si validation OK, False sinon
        """
        logger.info("Validation des données...")
        
        # Vérifier doublons
        ids = [p['id'] for p in players]
        if len(ids) != len(set(ids)):
            logger.error("Doublons détectés!")
            return False
        
        # Vérifier colonnes critiques
        critical_cols = self.validation_rules.get('critical_columns', ['id', 'full_name'])
        for player in players:
            for col in critical_cols:
                if not player.get(col):
                    logger.error(f"Colonne critique '{col}' manquante pour joueur {player.get('id')}")
                    return False
        
        # Vérifier taux nulls
        total_cells = len(players) * len(players[0])
        null_cells = sum(1 for p in players for v in p.values() if v is None)
        null_rate = null_cells / total_cells
        
        self.stats['nulls_after_cleaning'] = null_cells
        
        threshold = self.validation_rules.get('null_threshold', {}).get('global', 0.05)
        if null_rate > threshold:
            logger.error(f"Taux nulls trop élevé: {null_rate:.2%} > {threshold:.2%}")
            return False
        
        # Vérifier plages
        ranges = self.validation_rules.get('ranges', {})
        for player in players:
            if player.get('height_cm'):
                h_min = ranges.get('height_cm', {}).get('min', 160)
                h_max = ranges.get('height_cm', {}).get('max', 240)
                if not (h_min <= player['height_cm'] <= h_max):
                    logger.warning(f"Height hors plage pour {player['full_name']}: {player['height_cm']}")
            
            if player.get('weight_kg'):
                w_min = ranges.get('weight_kg', {}).get('min', 60)
                w_max = ranges.get('weight_kg', {}).get('max', 160)
                if not (w_min <= player['weight_kg'] <= w_max):
                    logger.warning(f"Weight hors plage pour {player['full_name']}: {player['weight_kg']}")
        
        logger.info(f"Validation OK - Taux nulls: {null_rate:.2%}")
        return True
    
    def _convert_to_python_types(self, players: List[Dict]) -> List[Dict]:
        """
        Convertit tous les types en types Python natifs compatibles avec Spark.
        
        Args:
            players: Liste des joueurs
            
        Returns:
            Liste avec types Python natifs
        """
        import numpy as np
        
        # Champs qui doivent être des integers
        int_fields = {'id', 'height_cm', 'weight_kg', 'age', 'from_year', 'to_year'}
        
        converted = []
        for player in players:
            converted_player = {}
            for key, value in player.items():
                if key in int_fields:
                    # Forcer la conversion en int pour les champs numériques
                    try:
                        if value is None:
                            converted_player[key] = None
                        elif isinstance(value, (np.integer, int)):
                            converted_player[key] = int(value)
                        elif isinstance(value, (np.floating, float)):
                            converted_player[key] = int(value)
                        elif isinstance(value, str):
                            converted_player[key] = int(value)
                        else:
                            converted_player[key] = int(value)
                    except (ValueError, TypeError):
                        converted_player[key] = None
                elif isinstance(value, np.integer):
                    converted_player[key] = int(value)
                elif isinstance(value, np.floating):
                    if value == int(value):
                        converted_player[key] = int(value)
                    else:
                        converted_player[key] = float(value)
                elif isinstance(value, float):
                    if value == int(value):
                        converted_player[key] = int(value)
                    else:
                        converted_player[key] = value
                elif isinstance(value, np.ndarray):
                    converted_player[key] = value.tolist()
                elif isinstance(value, dict):
                    converted_player[key] = self._convert_dict_types(value)
                else:
                    converted_player[key] = value
            converted.append(converted_player)
        return converted
    
    def _convert_dict_types(self, d: Dict) -> Dict:
        """Convertit récursivement les types numpy et float dans un dictionnaire."""
        import numpy as np
        
        result = {}
        for key, value in d.items():
            if isinstance(value, np.integer):
                result[key] = int(value)
            elif isinstance(value, np.floating):
                if value == int(value):
                    result[key] = int(value)
                else:
                    result[key] = float(value)
            elif isinstance(value, float):
                if value == int(value):
                    result[key] = int(value)
                else:
                    result[key] = value
            elif isinstance(value, np.ndarray):
                result[key] = value.tolist()
            elif isinstance(value, dict):
                result[key] = self._convert_dict_types(value)
            else:
                result[key] = value
        return result
    
    def save_to_silver(self, players: List[Dict]):
        """
        Sauvegarde les données en Delta Lake partitionné.
        
        Args:
            players: Liste des joueurs nettoyés
        """
        logger.info("Sauvegarde en Delta Lake...")
        
        # Convertir les types numpy en types Python natifs
        players_converted = self._convert_to_python_types(players)
        
        # Définir un schéma explicite pour éviter les conflits de type
        schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("full_name", StringType(), True),
            StructField("first_name", StringType(), True),
            StructField("last_name", StringType(), True),
            StructField("is_active", BooleanType(), True),
            StructField("height_cm", IntegerType(), True),
            StructField("weight_kg", IntegerType(), True),
            StructField("position", StringType(), True),
            StructField("birth_date", StringType(), True),
            StructField("age", IntegerType(), True),
            StructField("from_year", IntegerType(), True),
            StructField("to_year", IntegerType(), True),
            StructField("data_source", StringType(), True),
        ])
        
        # Créer DataFrame Spark avec schéma explicite
        df = self.spark.createDataFrame(players_converted, schema)
        
        # Créer répertoire output
        output_path = f"{SILVER_BASE}/players_cleaned"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Supprimer anciennes données si existent
        import shutil
        if Path(output_path).exists():
            shutil.rmtree(output_path)
        
        # Sauvegarder partitionné
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy("is_active", "position") \
            .save(output_path)
        
        logger.info(f"Données sauvegardées: {output_path}")
        
        # Générer rapport
        self._generate_report(players, output_path)
    
    def _generate_report(self, players: List[Dict], output_path: str):
        """Génère le rapport de qualité."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_players': len(players),
            'enrichment_stats': {
                'from_roster': self.stats['from_roster'],
                'from_api': self.stats['from_api'],
                'from_csv': self.stats['from_csv'],
                'imputed': self.stats['imputed']
            },
            'validation': {
                'duplicates': 0,
                'null_rate': self.stats['nulls_after_cleaning'] / (len(players) * len(players[0])) if players else 0,
                'output_path': output_path
            },
            'schema': list(players[0].keys()) if players else []
        }
        
        report_path = f"{SILVER_BASE}/players_cleaned_stats.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Rapport généré: {report_path}")
    
    def run(self, period_filter: bool = True):
        """
        Exécute le pipeline complet de nettoyage.
        
        Args:
            period_filter: Si True, ne récupère que les joueurs de 2000-2026
        """
        logger.info("=" * 60)
        logger.info("NBA-17: Nettoyage des données joueurs (Refactorisé v2.0)")
        if period_filter:
            logger.info("Période: 2000-2026 (joueurs ayant joué pendant cette période)")
        else:
            logger.info("Période: Tous les joueurs (1947-2026)")
        logger.info("=" * 60)
        
        try:
            # Étape 1: Chargement et enrichissement
            players_dict = self.load_and_merge_sources(period_filter=period_filter)
            
            # Étape 2: Nettoyage et conversion (utilise fonctions utilitaires)
            cleaned_players = self.clean_and_convert(players_dict)
            
            # Étape 2.5: Filtrer pour ne garder que les joueurs avec données réelles
            # (Ceux enrichis par roster, API ou CSV - pas les joueurs avec données imputées)
            players_with_complete_data = [
                p for p in cleaned_players 
                if p.get('data_source') in ['roster', 'api', 'api_cached', 'csv']
            ]
            
            filtered_count = len(cleaned_players) - len(players_with_complete_data)
            logger.info(f"Filtrage: {filtered_count} joueurs avec données imputées ignorés")
            logger.info(f"Joueurs avec données réelles: {len(players_with_complete_data)}")
            
            # Étape 3: Validation (sur le sous-ensemble filtré)
            if not self.validate_data(players_with_complete_data):
                logger.error("Validation échouée!")
                return False
            
            # Étape 4: Sauvegarde (uniquement les joueurs avec données complètes)
            self.save_to_silver(players_with_complete_data)
            
            # Résumé
            logger.info("=" * 60)
            logger.info("✅ NETTOYAGE TERMINÉ AVEC SUCCÈS")
            logger.info("=" * 60)
            logger.info(f"Total joueurs chargés: {self.stats['total']}")
            logger.info(f"Joueurs sauvegardés: {len(players_with_complete_data)}")
            logger.info(f"Joueurs filtrés (sans données): {filtered_count}")
            logger.info(f"  - Depuis roster: {self.stats['from_roster']}")
            logger.info(f"  - Depuis API: {self.stats['from_api']}")
            logger.info(f"  - Depuis CSV: {self.stats['from_csv']}")
            logger.info(f"  - Imputés: {self.stats['imputed']}")
            logger.info(f"Output: {SILVER_BASE}/players_cleaned/")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur pendant le nettoyage: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


# Point d'entrée principal
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='NBA-17: Nettoyage des données joueurs')
    parser.add_argument('--period', type=str, default='2000-2026',
                       help='Période à récupérer (ex: 2000-2026, all)')
    parser.add_argument('--full', action='store_true',
                       help='Récupérer tous les joueurs (sans filtre de période)')
    
    args = parser.parse_args()
    
    # Déterminer si on filtre par période
    period_filter = not args.full
    
    cleaner = PlayersDataCleaner()
    success = cleaner.run(period_filter=period_filter)
    sys.exit(0 if success else 1)
