"""
Pipeline complet Bronze → Silver → Gold pour les données joueurs.

Orchestre l'exécution complète avec gestion d'erreurs et reporting.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processing.bronze import PlayersBronze, BronzeValidator
from processing.silver import PlayersSilver
from processing.silver.data_mesh_stratifier import (
    DataMeshStratifier, DataProduct, QualityLevel
)
from processing.gold import PlayersGold

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlayersPipeline:
    """
    Pipeline orchestrateur complet avec support stratification.
    
    Modes:
        - Legacy: Un seul dataset Silver (retro-compatible)
        - Stratified: 3 datasets Silver (all, intermediate, contemporary)
    
    Usage:
        pipeline = PlayersPipeline(use_stratification=True)
        pipeline.run_full_pipeline(target='contemporary')
    """
    
    def __init__(self, use_stratification: bool = False):
        """
        Initialise les composants du pipeline.
        
        Args:
            use_stratification: Active le mode 3 datasets (feature flag)
        """
        self.use_stratification = use_stratification
        self.bronze = PlayersBronze()
        self.silver = PlayersSilver()
        self.gold = PlayersGold()
        
        self.execution_stats = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0,
            'steps': {}
        }
    
    def run_bronze_layer(self, period_filter: bool = True) -> bool:
        """
        Exécute la couche Bronze.
        
        Returns:
            True si succès
        """
        step_name = "Bronze Layer"
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP: {step_name}")
        logger.info(f"{'='*60}\n")
        
        start = time.time()
        
        try:
            # Exécuter Bronze
            players = self.bronze.run_bronze_layer(period_filter)
            
            # Valider
            validator = BronzeValidator()
            if not validator.validate(players):
                logger.error(f"❌ {step_name} validation échouée")
                return False
            
            duration = time.time() - start
            self.execution_stats['steps'][step_name] = {
                'status': 'success',
                'duration_seconds': duration,
                'players_count': len(players)
            }
            
            logger.info(f"✅ {step_name} terminé ({duration:.1f}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ {step_name} échoué: {e}")
            self.execution_stats['steps'][step_name] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def run_silver_layer(self, target: Optional[str] = None) -> bool:
        """
        Exécute la couche Silver.
        
        Args:
            target: Dataset cible en mode stratifie ('all', 'intermediate', 'contemporary')
                   Si None, cree tous les datasets en mode stratifie
        
        Returns:
            True si succès
        """
        step_name = "Silver Layer"
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP: {step_name}")
        if self.use_stratification:
            logger.info(f"Mode: Stratifie (target={target or 'all'})")
        else:
            logger.info(f"Mode: Legacy (mono-dataset)")
        logger.info(f"{'='*60}\n")
        
        start = time.time()
        
        try:
            if not self.use_stratification:
                # Mode legacy: comportement original
                players = self.silver.run_silver_layer()
                
                duration = time.time() - start
                self.execution_stats['steps'][step_name] = {
                    'status': 'success',
                    'duration_seconds': duration,
                    'players_count': len(players)
                }
                
                logger.info(f"✅ {step_name} termine ({duration:.1f}s)")
                return True
            
            # Mode stratifie: creer 3 datasets
            return self._run_stratified_silver(target)
            
        except Exception as e:
            logger.error(f"❌ {step_name} echoue: {e}")
            self.execution_stats['steps'][step_name] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def _run_stratified_silver(self, target: Optional[str] = None) -> bool:
        """
        Execute la couche Silver avec Architecture Data Mesh (7 datasets GOLD Tiered).
        
        Args:
            target: Dataset specifique ou None pour tous
                   Options: 'all', 'gold_premium', 'gold_standard', 'gold_basic'
        """
        # Initialiser stratifier Data Mesh
        logger.info("Initialisation Data Mesh Stratifier...")
        stratifier = DataMeshStratifier()
        
        # Recuperer les donnees Bronze
        bronze_data = self.silver.load_bronze()
        
        # Nettoyer d'abord toutes les donnees
        logger.info("Nettoyage des donnees Bronze...")
        cleaned_data = self.silver.clean_players(bronze_data)
        
        # Stratifier avec Data Mesh (creer 7 datasets avec GOLD Tiered)
        logger.info("Stratification Data Mesh en cours (GOLD Tiered)...")
        products = stratifier.stratify(cleaned_data)
        
        # Generer rapports qualite
        logger.info("Generation rapports qualite...")
        quality_report = stratifier.generate_quality_report(products)
        stratifier.export_report_json(quality_report)
        stratifier.export_lineage(products)
        
        # Sauvegarder chaque produit
        success_count = 0
        
        # Déterminer quels produits sauvegarder
        if target == 'all' or target is None:
            target_products = list(products.keys())
        elif target == 'gold':
            # Sauvegarder tous les datasets GOLD (3 tiers + legacy)
            target_products = ['gold_premium', 'gold_standard', 'gold_basic', 'gold']
        elif target in products:
            target_products = [target]
        else:
            logger.warning(f"Target inconnu: {target}, sauvegarde de tous les produits")
            target_products = list(products.keys())
        
        for product_name in target_products:
            if product_name not in products:
                logger.warning(f"Produit '{product_name}' non disponible, ignoré")
                continue
            
            product = products[product_name]
            output_path = product.config.get('output_path', f'data/silver/{product_name}/')
            
            # Affichage spécial pour GOLD Tiered
            if 'gold' in product_name:
                tier = product_name.replace('players_gold_', '').replace('players_gold', 'legacy')
                logger.info(f"\n🏆 GOLD TIER [{tier.upper():10}]:")
            else:
                logger.info(f"\nTraitement produit '{product_name}' [{product.quality_level.value}]:")
            
            logger.info(f"  Joueurs: {len(product.players)}")
            logger.info(f"  Completude: {product.stats['completeness_pct']:.1f}%")
            logger.info(f"  Taux nulls: {product.stats['null_rate']*100:.2f}%")
            
            # Sauvegarder (passer données simples, pas l'objet DataProduct)
            self._save_players_simple(
                players=product.players,
                output_path=output_path,
                product_name=product_name,
                quality_level=product.quality_level.value
            )
            
            logger.info(f"✅ Produit '{product_name}' sauvegarde: {output_path}")
            success_count += 1
        
        # Log resume GOLD Tiered
        logger.info(f"\n{'='*60}")
        logger.info(f"DATA MESH - GOLD TIERED RESUME")
        logger.info(f"{'='*60}")
        
        # Compter GOLD total
        gold_total = 0
        for tier in ['gold_premium', 'gold_standard', 'gold_basic']:
            if tier in products:
                count = len(products[tier].players)
                gold_total += count
                tier_name = tier.replace('gold_', '').upper()
                logger.info(f"GOLD {tier_name:8}: {count:4} joueurs")
        
        logger.info(f"{'':15} {'='*25}")
        logger.info(f"GOLD TOTAL:     {gold_total:4} joueurs")
        logger.info(f"{'='*60}")
        logger.info(f"Produits crees: {success_count}/{len(target_products)}")
        logger.info(f"Taux reduction RAW→GOLD: {quality_report['global_metrics']['data_reduction_rate']:.1f}%")
        logger.info(f"Rapport qualite: data/gold/data_quality_report.json")
        logger.info(f"Lineage: data/gold/lineage.json")
        
        return success_count == len(target_products)
    
    def _save_players_simple(self, players: List[Dict], output_path: str, 
                            product_name: str, quality_level: str) -> None:
        """
        Sauvegarde des joueurs en JSON (évite problèmes Spark).
        
        Args:
            players: Liste des joueurs
            output_path: Chemin de sortie
            product_name: Nom du produit
            quality_level: Niveau de qualité
        """
        from pathlib import Path
        import json
        from datetime import datetime
        
        # Creer repertoire
        path = Path(output_path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder données en JSON
        data_file = path / 'players.json'
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({'data': players}, f, indent=2, ensure_ascii=False, default=str)
        
        # Sauvegarder métadonnées
        metadata = {
            'product_name': product_name,
            'quality_level': quality_level,
            'player_count': len(players),
            'created_at': datetime.now().isoformat(),
            'output_path': str(path)
        }
        
        metadata_path = path / '_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Sauvegarde JSON: {data_file} ({len(players)} joueurs)")
        
        logger.info(f"Sauvegarde: {path} ({len(players)} joueurs)")
    
    def run_gold_layer(self) -> bool:
        """
        Exécute la couche Gold.
        
        Returns:
            True si succès
        """
        step_name = "Gold Layer"
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP: {step_name}")
        logger.info(f"{'='*60}\n")
        
        start = time.time()
        
        try:
            df = self.gold.run_gold_layer()
            
            duration = time.time() - start
            self.execution_stats['steps'][step_name] = {
                'status': 'success',
                'duration_seconds': duration,
                'players_count': df.count()
            }
            
            logger.info(f"✅ {step_name} terminé ({duration:.1f}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ {step_name} échoué: {e}")
            self.execution_stats['steps'][step_name] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def run_full_pipeline(self, period_filter: bool = True, target: Optional[str] = None) -> bool:
        """
        Execute le pipeline complet Bronze → Silver → Gold.
        
        Args:
            period_filter: Si True, filtre les joueurs anciens
            target: Dataset cible en mode stratifie ('all', 'intermediate', 'contemporary')
            
        Returns:
            True si tout le pipeline reussit
        """
        logger.info("\n" + "="*60)
        logger.info("NBA PIPELINE - Bronze -> Silver -> Gold")
        if self.use_stratification:
            logger.info(f"Mode: Stratifie (target={target or 'all'})")
        else:
            logger.info("Mode: Legacy")
        logger.info("="*60 + "\n")
        
        self.execution_stats['start_time'] = time.time()
        overall_start = time.time()
        
        # Bronze
        if not self.run_bronze_layer(period_filter):
            logger.error("\n❌ Pipeline arrete apres echec Bronze")
            return False
        
        # Silver
        if not self.run_silver_layer(target=target):
            logger.error("\n❌ Pipeline arrete apres echec Silver")
            return False
        
        # Gold (seulement en mode legacy ou si target='contemporary')
        if not self.use_stratification or target == 'contemporary':
            if not self.run_gold_layer():
                logger.error("\n❌ Pipeline arrete apres echec Gold")
                return False
        
        # Finalisation
        self.execution_stats['end_time'] = time.time()
        self.execution_stats['duration_seconds'] = time.time() - overall_start
        
        self._print_summary()
        
        logger.info("\n" + "="*60)
        logger.info("✅ PIPELINE TERMINE AVEC SUCCES")
        logger.info("="*60 + "\n")
        
        return True
    
    def _print_summary(self):
        """Affiche le résumé d'exécution."""
        logger.info("\n" + "="*60)
        logger.info("RÉSUMÉ D'EXÉCUTION")
        logger.info("="*60)
        
        total_duration = self.execution_stats['duration_seconds']
        logger.info(f"\nDurée totale: {total_duration:.1f} secondes")
        
        for step_name, stats in self.execution_stats['steps'].items():
            status = stats.get('status', 'unknown')
            duration = stats.get('duration_seconds', 0)
            count = stats.get('players_count', 0)
            
            icon = "✅" if status == 'success' else "❌"
            logger.info(f"\n{icon} {step_name}")
            logger.info(f"   Statut: {status}")
            logger.info(f"   Durée: {duration:.1f}s")
            logger.info(f"   Joueurs: {count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NBA Players Pipeline")
    parser.add_argument('--stratified', action='store_true',
                       help='Active le mode 3 datasets (all, intermediate, contemporary)')
    parser.add_argument('--target', choices=['all', 'intermediate', 'contemporary'],
                       help='Dataset cible en mode stratifie')
    parser.add_argument('--legacy', action='store_true',
                       help='Mode legacy (mono-dataset, defaut)')
    
    args = parser.parse_args()
    
    # Mode stratifie si --stratified ou si --target specifie
    use_stratified = args.stratified or (args.target is not None)
    
    print("NBA Players Pipeline - Medallion Architecture")
    print(f"Mode: {'Stratifie' if use_stratified else 'Legacy'}")
    if args.target:
        print(f"Target: {args.target}")
    print("\n" + "="*60)
    
    # Executer
    pipeline = PlayersPipeline(use_stratification=use_stratified)
    success = pipeline.run_full_pipeline(target=args.target)
    
    sys.exit(0 if success else 1)
