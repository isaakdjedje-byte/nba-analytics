"""
Data Mesh Stratifier - Architecture Professionnelle 4 Niveaux.

Transforme les données Bronze en 5 datasets qualifiés:
- RAW: 5,103 joueurs (aucune validation)
- BRONZE: ~4,000 joueurs (champs de base)
- SILVER: ~1,500 joueurs (métriques NBA)
- GOLD: ~800 joueurs (100% complet pour ML)
- CONTEMPORARY_TIER2: ~263 joueurs (modernes partiels)

Usage:
    from processing.silver.data_mesh_stratifier import DataMeshStratifier
    
    stratifier = DataMeshStratifier()
    products = stratifier.stratify(players)
    
    # Sauvegarder et générer rapports
    for name, product in products.items():
        stratifier.save_product(product)
    
    report = stratifier.generate_quality_report(products)
"""

import logging
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Niveaux de qualité Data Mesh standardisés."""
    RAW = "raw"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    SILVER_TIER2 = "silver_tier2"


@dataclass
class DataProduct:
    """
    Représente un produit de données avec contrat de qualité.
    
    Attributes:
        name: Nom du produit (ex: players_gold)
        quality_level: Niveau de qualité (RAW, BRONZE, SILVER, GOLD)
        config: Configuration complète du produit
        players: Liste des joueurs inclus
        stats: Statistiques de qualité
        lineage: Historique des transformations
        created_at: Timestamp de création
    """
    name: str
    quality_level: QualityLevel
    config: Dict[str, Any]
    players: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    lineage: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        if not self.stats:
            self.stats = {
                'total_players': 0,
                'completeness_pct': 0.0,
                'null_rate': 0.0,
                'validation_passed': False,
                'missing_fields_count': 0
            }


class DataMeshStratifier:
    """
    Stratification professionnelle avec architecture Data Mesh.
    
    Produit 5 datasets avec qualité explicite et traçabilité complète.
    Supporte validation configurable, lineage tracking, et rapports qualité.
    
    Attributes:
        config: Configuration des produits de données
        lineage: Historique global des opérations
        
    Example:
        >>> stratifier = DataMeshStratifier()
        >>> products = stratifier.stratify(bronze_players)
        >>> print(f"GOLD dataset: {len(products['gold'].players)} joueurs")
    """
    
    DEFAULT_CONFIG_PATH = "configs/data_products.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le stratifier avec configuration.
        
        Args:
            config_path: Chemin vers data_products.yaml (défaut: configs/data_products.yaml)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config(self.config_path)
        self.products_config = self.config.get('data_products', {})
        self.critical_ids = set(self.config.get('critical_player_ids', []))
        self.quality_thresholds = self.config.get('quality_thresholds', {})
        self.global_lineage = []
        
        logger.info(f"DataMeshStratifier initialisé avec config: {self.config_path}")
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Charge configuration YAML avec validation."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Validation basique
            if 'data_products' not in config:
                raise ValueError("Config invalide: 'data_products' manquant")
            
            logger.info(f"Configuration chargée: {len(config['data_products'])} produits")
            return config
            
        except FileNotFoundError:
            logger.error(f"Fichier de configuration non trouvé: {path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Erreur parsing YAML: {e}")
            raise
    
    def stratify(self, players: List[Dict[str, Any]]) -> Dict[str, DataProduct]:
        """
        Stratifie les joueurs en 7 produits de données (Architecture GOLD Tiered).
        
        Pipeline:
        1. RAW: Tous les joueurs sans filtre
        2. BRONZE: Filtrage champs de base (30% complet)
        3. SILVER: Filtrage métriques disponibles (70% complet)
        4. GOLD PREMIUM: Joueurs modernes 100% complets (~150)
        5. GOLD STANDARD: Joueurs avec données physiques (~500)
        6. GOLD BASIC: Joueurs avec identité (~1000+)
        7. TIER2: Joueurs modernes partiels
        
        Args:
            players: Liste des joueurs depuis couche Bronze
            
        Returns:
            Dict de DataProduct avec clés: raw, bronze, silver, 
            gold_premium, gold_standard, gold_basic, contemporary_tier2
        """
        start_time = datetime.now()
        logger.info(f"="*60)
        logger.info(f"DATA MESH STRATIFICATION - GOLD TIERED")
        logger.info(f"="*60)
        logger.info(f"Input: {len(players)} joueurs")
        logger.info(f"")
        
        products = {}
        
        # 1. RAW - Tous les joueurs
        logger.info("[1/7] Création dataset RAW...")
        products['raw'] = self._create_raw_product(players)
        
        # 2. BRONZE - Champs de base requis
        logger.info("[2/7] Filtrage niveau BRONZE...")
        bronze_players = self._filter_by_quality(players, 'players_bronze')
        products['bronze'] = self._create_bronze_product(bronze_players)
        
        # 3. SILVER - Métriques calculées
        logger.info("[3/7] Filtrage niveau SILVER...")
        silver_players = self._filter_by_quality(bronze_players, 'players_silver')
        products['silver'] = self._create_silver_product(silver_players)
        
        # 4-6. GOLD TIERED - 3 niveaux de qualité
        logger.info("[4-6/7] Filtrage niveau GOLD (3 tiers)...")
        gold_products = self._stratify_gold_tiered(silver_players, bronze_players)
        products.update(gold_products)
        
        # 7. CONTEMPORARY TIER2 - Modernes partiels
        logger.info("[7/7] Création sous-catégorie TIER2...")
        # Exclure tous les joueurs déjà dans un tier GOLD
        all_gold_ids = set()
        for tier in ['gold_premium', 'gold_standard', 'gold_basic']:
            if tier in products:
                all_gold_ids.update(p['id'] for p in products[tier].players)
        
        tier2_players = self._extract_contemporary_tier2(players, all_gold_ids)
        if tier2_players:
            products['contemporary_tier2'] = self._create_tier2_product(tier2_players)
        
        # 8. GOLD Legacy (pour backward compatibility)
        logger.info("[8/8] Création GOLD Legacy (deprecated)...")
        products['gold'] = self._create_gold_legacy_product(
            products.get('gold_premium', DataProduct('', QualityLevel.GOLD, {})).players
        )
        
        # Finalisation
        duration = (datetime.now() - start_time).total_seconds()
        self._log_summary(products, duration)
        
        return products
    
    def _create_raw_product(self, players: List[Dict]) -> DataProduct:
        """Crée produit RAW sans validation."""
        config = self.products_config['players_raw']
        
        product = DataProduct(
            name='players_raw',
            quality_level=QualityLevel.RAW,
            config=config,
            players=players.copy()
        )
        
        product.stats = {
            'total_players': len(players),
            'completeness_pct': self._calculate_completeness(players),
            'validation_passed': True,  # RAW n'a pas de validation
            'null_rate': self._calculate_null_rate(players)
        }
        
        product.lineage.append({
            'step': 'raw_creation',
            'input_count': len(players),
            'output_count': len(players),
            'filter': 'none',
            'timestamp': datetime.now().isoformat()
        })
        
        return product
    
    def _filter_by_quality(self, players: List[Dict], product_name: str) -> List[Dict]:
        """Filtre joueurs selon critères qualité du produit."""
        config = self.products_config[product_name]
        validation = config.get('validation', {})
        
        if not validation.get('enabled', False):
            return players.copy()
        
        required_fields = validation.get('required_fields', [])
        null_threshold = validation.get('null_threshold', 0.10)
        completeness_min = validation.get('completeness_min', 80)
        
        filtered = []
        for player in players:
            # Vérifier champs requis
            present_fields = sum(1 for field in required_fields if player.get(field))
            completeness = (present_fields / len(required_fields)) * 100 if required_fields else 100
            
            # Calculer taux de nulls
            null_rate = self._calculate_player_null_rate(player)
            
            # Appliquer filtres
            if completeness >= completeness_min and null_rate <= null_threshold:
                filtered.append(player)
        
        logger.info(f"  {product_name}: {len(filtered)}/{len(players)} joueurs "
                   f"({len(filtered)/len(players)*100:.1f}%)")
        return filtered
    
    def _stratify_gold_tiered(self, silver_players: List[Dict], 
                             bronze_players: List[Dict]) -> Dict[str, DataProduct]:
        """
        Crée 3 niveaux de GOLD avec différents critères de qualité.
        
        Stratégie:
        - GOLD Premium: Joueurs SILVER avec métadonnées complètes (position, is_active, team_id)
        - GOLD Standard: Joueurs SILVER avec données physiques mais sans métadonnées complètes
        - GOLD Basic: Joueurs BRONZE qui ne sont pas dans SILVER (identité seule)
        
        Args:
            silver_players: Joueurs qualifiés SILVER (~635 joueurs)
            bronze_players: Tous les joueurs BRONZE (~5103 joueurs)
            
        Returns:
            Dict avec gold_premium, gold_standard, gold_basic
        """
        products = {}
        
        # Helper pour vérifier si une valeur est valide
        def is_valid(value) -> bool:
            if value is None:
                return False
            if isinstance(value, (int, float)) and value == 0:
                return False
            if isinstance(value, str) and value.strip() == '':
                return False
            if isinstance(value, bool):
                return True  # True/False sont valides
            return True
        
        # 1. GOLD PREMIUM: Joueurs SILVER avec toutes les métadonnées requises
        logger.info("  -> GOLD Premium (métadonnées complètes)...")
        premium_candidates = []
        for player in silver_players:
            # Vérifier champs Premium: position, is_active, team_id
            has_position = is_valid(player.get('position'))
            has_active = player.get('is_active') is not None  # Booléen peut être False
            has_team = is_valid(player.get('team_id'))
            
            if has_position and has_active and has_team:
                premium_candidates.append(player)
        
        products['gold_premium'] = self._create_quality_product(
            name='players_gold_premium',
            level=QualityLevel.GOLD,
            players=premium_candidates,
            previous_step='players_silver'
        )
        
        # 2. GOLD STANDARD: Joueurs SILVER avec height/weight mais sans métadonnées complètes
        logger.info("  -> GOLD Standard (données physiques)...")
        premium_ids = {p['id'] for p in premium_candidates}
        
        # Standard = joueurs SILVER avec height/weight qui ne sont pas Premium
        standard_candidates = []
        for player in silver_players:
            if player['id'] not in premium_ids:
                # Vérifier qu'ils ont des données physiques
                if player.get('height_cm') and player.get('weight_kg'):
                    standard_candidates.append(player)
        
        products['gold_standard'] = self._create_quality_product(
            name='players_gold_standard',
            level=QualityLevel.GOLD,
            players=standard_candidates,
            previous_step='players_silver'
        )
        
        # 3. GOLD BASIC: Joueurs BRONZE qui ne sont pas dans SILVER (identité seule)
        logger.info("  -> GOLD Basic (identité seule)...")
        silver_ids = {p['id'] for p in silver_players}
        basic_candidates = []
        for player in bronze_players:
            if player['id'] not in silver_ids:
                # Ces joueurs n'ont pas height/weight complets
                basic_candidates.append(player)
        
        products['gold_basic'] = self._create_quality_product(
            name='players_gold_basic',
            level=QualityLevel.GOLD,
            players=basic_candidates,
            previous_step='players_bronze'
        )
        
        # Log résumé
        total_gold = len(premium_candidates) + len(standard_candidates) + len(basic_candidates)
        logger.info(f"  GOLD Total: {total_gold} joueurs "
                   f"(P:{len(premium_candidates)} + S:{len(standard_candidates)} + B:{len(basic_candidates)})")
        
        return products
    
    def _filter_gold_quality(self, players: List[Dict]) -> List[Dict]:
        """Filtre strict pour GOLD Legacy (100% complet, 20% nulls max)."""
        config = self.products_config.get('players_gold', {})
        validation = config.get('validation', {})
        
        required_fields = validation.get('required_fields', [])
        null_threshold = validation.get('null_threshold', 0.20)
        
        if not required_fields:
            return players.copy()
        
        filtered = []
        for player in players:
            all_present = all(player.get(field) for field in required_fields)
            null_rate = self._calculate_player_null_rate(player)
            
            if all_present and null_rate <= null_threshold:
                filtered.append(player)
        
        logger.info(f"  players_gold: {len(filtered)}/{len(players)} joueurs "
                   f"({len(filtered)/len(players)*100:.1f}%)")
        return filtered
    
    def _create_gold_legacy_product(self, premium_players: List[Dict]) -> DataProduct:
        """Crée produit GOLD Legacy pour backward compatibility."""
        return self._create_quality_product(
            name='players_gold',
            level=QualityLevel.GOLD,
            players=premium_players.copy(),
            previous_step='players_gold_premium'
        )
    
    def _extract_contemporary_tier2(self, all_players: List[Dict], 
                                   gold_ids: set) -> List[Dict]:
        """
        Extrait joueurs modernes (ID >= 1620000) non présents dans GOLD.
        Ces joueurs ont des données partielles mais sont récents (2016+).
        """
        config = self.products_config.get('players_contemporary_tier2', {})
        validation = config.get('validation', {})
        required_basic = validation.get('required_fields', ['id', 'full_name', 'height_cm', 'weight_kg'])
        
        tier2 = []
        for player in all_players:
            player_id = player.get('id', 0)
            
            # ID moderne (2016+) ET pas dans GOLD
            if player_id >= 1620000 and player_id not in gold_ids:
                # Vérifier qu'on a au moins les champs de base
                if all(player.get(field) for field in required_basic):
                    tier2.append(player)
        
        logger.info(f"  players_contemporary_tier2: {len(tier2)} joueurs")
        return tier2
    
    def _create_bronze_product(self, players: List[Dict]) -> DataProduct:
        """Crée produit BRONZE."""
        return self._create_quality_product(
            name='players_bronze',
            level=QualityLevel.BRONZE,
            players=players,
            previous_step='players_raw'
        )
    
    def _create_silver_product(self, players: List[Dict]) -> DataProduct:
        """Crée produit SILVER."""
        return self._create_quality_product(
            name='players_silver',
            level=QualityLevel.SILVER,
            players=players,
            previous_step='players_bronze'
        )
    
    def _create_gold_product(self, players: List[Dict]) -> DataProduct:
        """Crée produit GOLD."""
        return self._create_quality_product(
            name='players_gold',
            level=QualityLevel.GOLD,
            players=players,
            previous_step='players_silver'
        )
    
    def _create_tier2_product(self, players: List[Dict]) -> DataProduct:
        """Crée produit CONTEMPORARY_TIER2."""
        return self._create_quality_product(
            name='players_contemporary_tier2',
            level=QualityLevel.SILVER_TIER2,
            players=players,
            previous_step='players_raw'
        )
    
    def _create_quality_product(self, name: str, level: QualityLevel,
                               players: List[Dict], previous_step: str) -> DataProduct:
        """Crée un DataProduct avec calcul des stats de qualité."""
        config = self.products_config[name]
        
        product = DataProduct(
            name=name,
            quality_level=level,
            config=config,
            players=players.copy()
        )
        
        # Calculer statistiques
        product.stats = {
            'total_players': len(players),
            'completeness_pct': self._calculate_completeness(players),
            'null_rate': self._calculate_null_rate(players),
            'validation_passed': len(players) > 0,
            'missing_fields_count': self._count_missing_fields(players, config)
        }
        
        # Lineage
        product.lineage.append({
            'step': f'{name}_creation',
            'input_step': previous_step,
            'output_count': len(players),
            'quality_level': level.value,
            'timestamp': datetime.now().isoformat(),
            'checksum': self._calculate_checksum(players)
        })
        
        return product
    
    def _calculate_completeness(self, players: List[Dict]) -> float:
        """Calcule pourcentage moyen de complétude."""
        if not players:
            return 0.0
        
        total_completeness = 0
        for player in players:
            total_fields = len(player)
            filled_fields = sum(1 for v in player.values() if v is not None)
            total_completeness += (filled_fields / total_fields * 100) if total_fields else 100
        
        return total_completeness / len(players)
    
    def _calculate_null_rate(self, players: List[Dict]) -> float:
        """Calcule taux global de nulls."""
        if not players:
            return 0.0
        
        total_cells = 0
        null_cells = 0
        
        for player in players:
            for value in player.values():
                total_cells += 1
                if value is None:
                    null_cells += 1
        
        return null_cells / total_cells if total_cells else 0.0
    
    def _calculate_player_null_rate(self, player: Dict) -> float:
        """Calcule taux de nulls pour un joueur."""
        total = len(player)
        nulls = sum(1 for v in player.values() if v is None)
        return nulls / total if total else 0.0
    
    def _count_missing_fields(self, players: List[Dict], config: Dict) -> int:
        """Compte champs critiques manquants."""
        required = config.get('validation', {}).get('required_fields', [])
        if not required or not players:
            return 0
        
        missing_count = 0
        for player in players:
            for field in required:
                if not player.get(field):
                    missing_count += 1
        
        return missing_count
    
    def _calculate_checksum(self, players: List[Dict]) -> str:
        """Calcule checksum pour traçabilité."""
        data = json.dumps(players, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def generate_quality_report(self, products: Dict[str, DataProduct]) -> Dict[str, Any]:
        """
        Génère rapport de qualité complet avec métriques détaillées.
        
        Returns:
            Dict avec timestamp, summary par produit, et métriques globales
        """
        report = {
            'report_version': '2.0',
            'generated_at': datetime.now().isoformat(),
            'pipeline': 'data-mesh-stratification',
            'summary': {
                'total_products': len(products),
                'total_source_players': sum(len(p.players) for p in products.values()),
                'validation_overall': all(p.stats.get('validation_passed', False) 
                                        for p in products.values())
            },
            'products': {}
        }
        
        for name, product in products.items():
            report['products'][name] = {
                'quality_level': product.quality_level.value,
                'player_count': len(product.players),
                'completeness_pct': round(product.stats['completeness_pct'], 2),
                'null_rate': round(product.stats['null_rate'] * 100, 2),
                'validation_passed': product.stats['validation_passed'],
                'output_path': product.config.get('output_path', 'N/A'),
                'lineage_steps': len(product.lineage)
            }
        
        # Métriques globales
        report['global_metrics'] = {
            'data_reduction_rate': self._calculate_reduction_rate(products),
            'quality_improvement': self._calculate_quality_improvement(products),
            'tier2_extraction': len(products.get('contemporary_tier2', DataProduct('', QualityLevel.RAW, {})).players)
        }
        
        return report
    
    def _calculate_reduction_rate(self, products: Dict[str, DataProduct]) -> float:
        """Calcule taux de réduction RAW → GOLD."""
        raw_count = len(products.get('raw', DataProduct('', QualityLevel.RAW, {})).players)
        gold_count = len(products.get('gold', DataProduct('', QualityLevel.GOLD, {})).players)
        
        if raw_count == 0:
            return 0.0
        
        return round((1 - gold_count / raw_count) * 100, 2)
    
    def _calculate_quality_improvement(self, products: Dict[str, DataProduct]) -> float:
        """Calcule amélioration qualité RAW → GOLD."""
        raw_completeness = products.get('raw', DataProduct('', QualityLevel.RAW, {})).stats.get('completeness_pct', 0)
        gold_completeness = products.get('gold', DataProduct('', QualityLevel.GOLD, {})).stats.get('completeness_pct', 0)
        
        return round(gold_completeness - raw_completeness, 2)
    
    def _log_summary(self, products: Dict[str, DataProduct], duration: float):
        """Affiche résumé stratification."""
        logger.info(f"")
        logger.info(f"="*60)
        logger.info(f"STRATIFICATION TERMINÉE - GOLD TIERED")
        logger.info(f"="*60)
        logger.info(f"Durée: {duration:.2f}s")
        logger.info(f"")
        
        # Afficher par niveau de qualité
        logger.info(f"Produits créés:")
        
        # RAW
        if 'raw' in products:
            p = products['raw']
            logger.info(f"  [RAW      ] {p.name:30} {len(p.players):5} joueurs "
                       f"({p.stats['completeness_pct']:.1f}% complet)")
        
        # BRONZE
        if 'bronze' in products:
            p = products['bronze']
            logger.info(f"  [BRONZE   ] {p.name:30} {len(p.players):5} joueurs "
                       f"({p.stats['completeness_pct']:.1f}% complet)")
        
        # SILVER
        if 'silver' in products:
            p = products['silver']
            logger.info(f"  [SILVER   ] {p.name:30} {len(p.players):5} joueurs "
                       f"({p.stats['completeness_pct']:.1f}% complet)")
        
        # GOLD TIERED (les 3 niveaux)
        gold_tiers = ['gold_premium', 'gold_standard', 'gold_basic']
        total_gold = 0
        for tier in gold_tiers:
            if tier in products:
                p = products[tier]
                total_gold += len(p.players)
                tier_name = tier.replace('gold_', '').upper()
                logger.info(f"  [GOLD-{tier_name:8}] {p.name:30} {len(p.players):5} joueurs "
                           f"({p.stats['completeness_pct']:.1f}% complet)")
        
        # Total GOLD
        logger.info(f"  {'':12} {'GOLD TOTAL':30} {total_gold:5} joueurs")
        
        # Legacy GOLD (deprecated)
        if 'gold' in products:
            p = products['gold']
            logger.info(f"  [GOLD-LEG ] {p.name:30} {len(p.players):5} joueurs "
                       f"(deprecated)")
        
        # TIER2
        if 'contemporary_tier2' in products:
            p = products['contemporary_tier2']
            logger.info(f"  [TIER2    ] {p.name:30} {len(p.players):5} joueurs "
                       f"({p.stats['completeness_pct']:.1f}% complet)")
        
        logger.info(f"="*60)
    
    def export_report_json(self, report: Dict[str, Any], 
                          output_path: str = "data/gold/data_quality_report.json"):
        """Exporte rapport en JSON."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Rapport qualité exporté: {path}")
    
    def export_lineage(self, products: Dict[str, DataProduct],
                      output_path: str = "data/gold/lineage.json"):
        """Exporte lineage simplifié (évite récursion)."""
        lineage_data = {
            'pipeline_version': '2.0',
            'generated_at': datetime.now().isoformat(),
            'products': {}
        }
        
        for name, product in products.items():
            # Extraire uniquement les champs simples du lineage
            simple_lineage = []
            for step in product.lineage:
                simple_step = {
                    'step': step.get('step', 'unknown'),
                    'timestamp': step.get('timestamp', ''),
                    'input_count': step.get('input_count', 0),
                    'output_count': step.get('output_count', 0)
                }
                simple_lineage.append(simple_step)
            
            lineage_data['products'][name] = {
                'quality_level': product.quality_level.value,
                'player_count': len(product.players),
                'lineage_steps': len(simple_lineage),
                'checksum': product.lineage[-1].get('checksum') if product.lineage else None
            }
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(lineage_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Lineage exporté: {path}")


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def quick_stratify(players: List[Dict[str, Any]]) -> Dict[str, DataProduct]:
    """
    Fonction rapide pour stratification sans configuration custom.
    
    Args:
        players: Liste des joueurs Bronze
        
    Returns:
        Dict de DataProduct prêts à l'emploi
    """
    stratifier = DataMeshStratifier()
    return stratifier.stratify(players)


def get_product_by_quality(products: Dict[str, DataProduct], 
                          level: QualityLevel) -> Optional[DataProduct]:
    """Récupère produit par niveau de qualité."""
    for product in products.values():
        if product.quality_level == level:
            return product
    return None


if __name__ == "__main__":
    # Test rapide
    print("Test DataMeshStratifier:")
    
    # Données test
    test_players = [
        {'id': 1, 'full_name': 'Complete Player', 'height_cm': 200, 
         'weight_kg': 100, 'position': 'F', 'is_active': True, 
         'team_id': 123, 'birth_date': '1990-01-01'},
        {'id': 2, 'full_name': 'Partial Player', 'height_cm': 195, 
         'weight_kg': 95},  # Manque champs
        {'id': 1626143, 'full_name': 'Modern Player', 'height_cm': 198,
         'weight_kg': 102, 'position': 'G', 'is_active': True},  # Moderne partiel
    ]
    
    stratifier = DataMeshStratifier()
    products = stratifier.stratify(test_players)
    
    print(f"\nRésultats:")
    for name, product in products.items():
        print(f"  {name}: {len(product.players)} joueurs "
              f"({product.stats['completeness_pct']:.1f}% complet)")
    
    report = stratifier.generate_quality_report(products)
    print(f"\nQualité globale: {report['summary']['validation_overall']}")
