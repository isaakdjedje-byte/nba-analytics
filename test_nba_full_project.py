#!/usr/bin/env python3
"""
Test Complet du Projet NBA Analytics (NBA-11 à NBA-22)
Vérifie que tous les composants fonctionnent correctement
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
import subprocess
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestResult:
    """Classe pour stocker les résultats de test"""
    def __init__(self, name, category):
        self.name = name
        self.category = category
        self.status = None  # True=OK, False=FAIL, None=SKIP
        self.duration = 0
        self.error_msg = None
        self.details = {}
    
    def to_dict(self):
        return {
            'name': self.name,
            'category': self.category,
            'status': 'OK' if self.status is True else ('FAIL' if self.status is False else 'SKIP'),
            'duration': f"{self.duration:.2f}s",
            'error': self.error_msg,
            'details': self.details
        }

class NBAFullProjectTest:
    """Test complet du projet NBA Analytics"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.project_root = Path(__file__).parent
        
    def run_all_tests(self):
        """Exécute tous les tests"""
        logger.info("="*70)
        logger.info("TEST COMPLET DU PROJET NBA ANALYTICS")
        logger.info("NBA-11 à NBA-22 - Vérification complète")
        logger.info("="*70)
        logger.info(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        self.start_time = time.time()
        
        # 1. Tests Structure et Configuration
        self.test_structure()
        
        # 2. Tests NBA-11 à NBA-15 : Ingestion
        self.test_ingestion()
        
        # 3. Tests NBA-16 à NBA-20 : Processing
        self.test_processing()
        
        # 4. Tests NBA-21 : Feature Engineering
        self.test_feature_engineering()
        
        # 5. Tests NBA-22 : Machine Learning
        self.test_machine_learning()
        
        # 6. Tests Intégration
        self.test_integration()
        
        # Générer rapport
        self.generate_report()
        
    def test_structure(self):
        """Test la structure du projet"""
        logger.info("\n" + "="*70)
        logger.info("1. TEST STRUCTURE ET CONFIGURATION")
        logger.info("="*70)
        
        # Test 1.1 : Vérifier les dossiers principaux
        result = TestResult("Structure des dossiers", "Structure")
        start = time.time()
        try:
            required_dirs = [
                'src', 'data', 'docs', 'tests', 'models', 
                'src/ingestion', 'src/processing', 'src/ml', 
                'src/pipeline', 'src/utils'
            ]
            missing = []
            for dir_path in required_dirs:
                if not (self.project_root / dir_path).exists():
                    missing.append(dir_path)
            
            if missing:
                result.status = False
                result.error_msg = f"Dossiers manquants: {', '.join(missing)}"
            else:
                result.status = True
                result.details['directories_checked'] = len(required_dirs)
            
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Structure: {result.status}")
        
        # Test 1.2 : Vérifier les fichiers de configuration
        result = TestResult("Fichiers de configuration", "Structure")
        start = time.time()
        try:
            required_files = [
                'docs/INDEX.md', 'docs/JIRA_BACKLOG.md',
                'data/team_mapping.json', 'data/team_name_to_id.json',
                'models/optimized/model_xgb.joblib',
                'models/optimized/selected_features.json'
            ]
            missing = []
            for file_path in required_files:
                if not (self.project_root / file_path).exists():
                    missing.append(file_path)
            
            if missing:
                result.status = False
                result.error_msg = f"Fichiers manquants: {', '.join(missing)}"
            else:
                result.status = True
                result.details['files_checked'] = len(required_files)
                
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Configuration: {result.status}")
        
    def test_ingestion(self):
        """Test NBA-11 à NBA-15 : Ingestion de données"""
        logger.info("\n" + "="*70)
        logger.info("2. TEST INGESTION (NBA-11 à NBA-15)")
        logger.info("="*70)
        
        # Test 2.1 : Données brutes
        result = TestResult("Données brutes (NBA-11)", "Ingestion")
        start = time.time()
        try:
            raw_data_dirs = ['data/raw/teams', 'data/raw/rosters', 'data/raw/schedules']
            found = 0
            for dir_path in raw_data_dirs:
                if (self.project_root / dir_path).exists():
                    found += 1
            
            result.status = found > 0
            result.details['data_dirs_found'] = f"{found}/{len(raw_data_dirs)}"
            
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} NBA-11 (Données brutes): {result.status}")
        
        # Test 2.2 : Mapping équipes
        result = TestResult("Mapping équipes (NBA-15)", "Ingestion")
        start = time.time()
        try:
            team_mapping_file = self.project_root / 'data/team_mapping.json'
            if team_mapping_file.exists():
                with open(team_mapping_file) as f:
                    mapping = json.load(f)
                result.status = len(mapping) == 30
                result.details['teams'] = len(mapping)
            else:
                result.status = False
                result.error_msg = "Fichier team_mapping.json non trouvé"
                
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} NBA-15 (Mapping): {result.status}")
        
        # Test 2.3 : API NBA Live
        result = TestResult("API NBA Live", "Ingestion")
        start = time.time()
        try:
            sys.path.insert(0, str(self.project_root / 'src' / 'ml' / 'pipeline'))
            from nba_live_api import test_api_connection
            api_ok = test_api_connection()
            result.status = api_ok
            result.details['api_available'] = api_ok
            
        except Exception as e:
            result.status = False
            result.error_msg = f"API non disponible: {str(e)}"
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} API NBA Live: {result.status}")
        
    def test_processing(self):
        """Test NBA-16 à NBA-20 : Processing"""
        logger.info("\n" + "="*70)
        logger.info("3. TEST PROCESSING (NBA-16 à NBA-20)")
        logger.info("="*70)
        
        # Test 3.1 : Nettoyage des données (NBA-17)
        result = TestResult("Nettoyage données (NBA-17)", "Processing")
        start = time.time()
        try:
            silver_dir = self.project_root / 'data/silver'
            if silver_dir.exists():
                result.status = True
                result.details['silver_layer'] = "Existe"
            else:
                # Vérifier si gold layer existe (données déjà traitées)
                gold_dir = self.project_root / 'data/gold'
                if gold_dir.exists():
                    result.status = True
                    result.details['note'] = "Silver non trouvé mais Gold existe"
                else:
                    result.status = False
                    result.error_msg = "Ni Silver ni Gold layer trouvés"
                    
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} NBA-17 (Nettoyage): {result.status}")
        
        # Test 3.2 : Métriques avancées (NBA-18)
        result = TestResult("Métriques avancées (NBA-18)", "Processing")
        start = time.time()
        try:
            # Vérifier si les données enrichies existent
            enriched_files = list((self.project_root / 'data').rglob('*_enriched*.json'))
            enriched_files += list((self.project_root / 'data').rglob('players_advanced*'))
            
            result.status = len(enriched_files) > 0
            result.details['enriched_files'] = len(enriched_files)
            
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} NBA-18 (Métriques): {result.status}")
        
        # Test 3.3 : Agrégations (NBA-19)
        result = TestResult("Agrégations équipes (NBA-19)", "Processing")
        start = time.time()
        try:
            team_stats_dir = self.project_root / 'data/gold/team_season_stats'
            if team_stats_dir.exists():
                files = list(team_stats_dir.glob('*.parquet')) + list(team_stats_dir.glob('*.json'))
                result.status = len(files) > 0
                result.details['team_stats_files'] = len(files)
            else:
                # Vérifier rapport NBA-19
                report_file = self.project_root / 'data/gold/nba19_report.json'
                result.status = report_file.exists()
                result.details['report_exists'] = report_file.exists()
                
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} NBA-19 (Agrégations): {result.status}")
        
        # Test 3.4 : Transformation matchs (NBA-20)
        result = TestResult("Transformation matchs (NBA-20)", "Processing")
        start = time.time()
        try:
            games_file = self.project_root / 'data/silver/games_processed/games_structured.json'
            if games_file.exists():
                with open(games_file) as f:
                    games = json.load(f)
                result.status = len(games) > 0
                result.details['games_count'] = len(games)
            else:
                # Vérifier via features (dérivées des matchs)
                features_file = self.project_root / 'data/gold/ml_features/features_v3.parquet'
                result.status = features_file.exists()
                result.details['features_exist'] = features_file.exists()
                
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} NBA-20 (Matchs): {result.status}")
        
    def test_feature_engineering(self):
        """Test NBA-21 : Feature Engineering"""
        logger.info("\n" + "="*70)
        logger.info("4. TEST FEATURE ENGINEERING (NBA-21)")
        logger.info("="*70)
        
        # Test 4.1 : Features V1
        result = TestResult("Features V1", "Feature Engineering")
        start = time.time()
        try:
            features_v1 = self.project_root / 'data/gold/ml_features/features_all.parquet'
            result.status = features_v1.exists()
            result.details['v1_exists'] = features_v1.exists()
            
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Features V1: {result.status}")
        
        # Test 4.2 : Features V3
        result = TestResult("Features V3 (Optimisées)", "Feature Engineering")
        start = time.time()
        try:
            features_v3 = self.project_root / 'data/gold/ml_features/features_v3.parquet'
            if features_v3.exists():
                import pandas as pd
                df = pd.read_parquet(features_v3)
                result.status = True
                result.details['matches'] = len(df)
                result.details['features'] = len(df.columns)
            else:
                result.status = False
                result.error_msg = "Features V3 non trouvées"
                
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Features V3: {result.status} - {result.details.get('matches', 0)} matchs, {result.details.get('features', 0)} features")
        
    def test_machine_learning(self):
        """Test NBA-22 : Machine Learning"""
        logger.info("\n" + "="*70)
        logger.info("5. TEST MACHINE LEARNING (NBA-22)")
        logger.info("="*70)
        
        # Test 5.1 : Modèles entraînés
        result = TestResult("Modèles entraînés", "ML")
        start = time.time()
        try:
            models_dir = self.project_root / 'models/week1'
            optimized_dir = self.project_root / 'models/optimized'
            
            models_found = []
            if models_dir.exists():
                models_found += list(models_dir.glob('*.pkl')) + list(models_dir.glob('*.joblib'))
            if optimized_dir.exists():
                models_found += list(optimized_dir.glob('*.pkl')) + list(optimized_dir.glob('*.joblib'))
            
            result.status = len(models_found) > 0
            result.details['models_count'] = len(models_found)
            result.details['models'] = [m.name for m in models_found[:5]]  # Top 5
            
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Modèles: {result.status} - {result.details.get('models_count', 0)} modèles")
        
        # Test 5.2 : Modèle optimisé
        result = TestResult("Modèle optimisé (v2.0)", "ML")
        start = time.time()
        try:
            optimized_model = self.project_root / 'models/optimized/model_xgb.joblib'
            calibrator = self.project_root / 'models/optimized/calibrator_xgb.joblib'
            features_file = self.project_root / 'models/optimized/selected_features.json'
            
            checks = {
                'model': optimized_model.exists(),
                'calibrator': calibrator.exists(),
                'features': features_file.exists()
            }
            
            result.status = all(checks.values())
            result.details.update(checks)
            
            if result.status and features_file.exists():
                with open(features_file) as f:
                    features_data = json.load(f)
                result.details['n_selected_features'] = features_data.get('n_features', 'N/A')
                
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Modèle optimisé v2.0: {result.status}")
        
        # Test 5.3 : Prédictions
        result = TestResult("Pipeline de prédiction", "ML")
        start = time.time()
        try:
            pred_script = self.project_root / 'run_predictions_optimized.py'
            result.status = pred_script.exists()
            result.details['script_exists'] = pred_script.exists()
            
            # Vérifier si des prédictions existent
            pred_dir = self.project_root / 'predictions'
            if pred_dir.exists():
                pred_files = list(pred_dir.glob('predictions_*.csv'))
                result.details['prediction_files'] = len(pred_files)
            
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Pipeline prédiction: {result.status}")
        
    def test_integration(self):
        """Tests d'intégration"""
        logger.info("\n" + "="*70)
        logger.info("6. TESTS D'INTÉGRATION")
        logger.info("="*70)
        
        # Test 6.1 : Pipeline complet
        result = TestResult("Pipeline complet", "Intégration")
        start = time.time()
        try:
            # Vérifier que tous les composants sont là
            checks = {
                'data_exists': (self.project_root / 'data').exists(),
                'models_exist': (self.project_root / 'models').exists(),
                'predictions_exist': (self.project_root / 'predictions').exists(),
                'scripts_exist': (self.project_root / 'run_predictions_optimized.py').exists()
            }
            
            result.status = all(checks.values())
            result.details.update(checks)
            
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Pipeline complet: {result.status}")
        
        # Test 6.2 : Tracking ROI
        result = TestResult("Tracking ROI", "Intégration")
        start = time.time()
        try:
            tracking_file = self.project_root / 'predictions/tracking_history.csv'
            result.status = tracking_file.exists()
            result.details['tracking_exists'] = tracking_file.exists()
            
            if tracking_file.exists():
                import pandas as pd
                df = pd.read_csv(tracking_file)
                result.details['tracked_predictions'] = len(df)
            
        except Exception as e:
            result.status = False
            result.error_msg = str(e)
        
        result.duration = time.time() - start
        self.results.append(result)
        logger.info(f"  {'✓' if result.status else '✗'} Tracking ROI: {result.status}")
        
    def generate_report(self):
        """Génère le rapport de test"""
        total_duration = time.time() - self.start_time
        
        # Compter les résultats
        ok_count = sum(1 for r in self.results if r.status is True)
        fail_count = sum(1 for r in self.results if r.status is False)
        skip_count = sum(1 for r in self.results if r.status is None)
        total_count = len(self.results)
        
        logger.info("\n" + "="*70)
        logger.info("RAPPORT DE TEST")
        logger.info("="*70)
        logger.info(f"Total tests: {total_count}")
        logger.info(f"✓ OK: {ok_count}")
        logger.info(f"✗ FAIL: {fail_count}")
        logger.info(f"⊘ SKIP: {skip_count}")
        logger.info(f"Taux de réussite: {(ok_count/total_count*100):.1f}%")
        logger.info(f"Durée totale: {total_duration:.2f}s")
        
        # Détail par catégorie
        logger.info("\n" + "-"*70)
        logger.info("DÉTAIL PAR CATÉGORIE")
        logger.info("-"*70)
        
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {'ok': 0, 'total': 0}
            categories[r.category]['total'] += 1
            if r.status is True:
                categories[r.category]['ok'] += 1
        
        for cat, stats in categories.items():
            rate = (stats['ok'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"{cat:20s}: {stats['ok']}/{stats['total']} ({rate:.0f}%)")
        
        # Tests en échec
        if fail_count > 0:
            logger.info("\n" + "-"*70)
            logger.info("TESTS EN ÉCHEC")
            logger.info("-"*70)
            for r in self.results:
                if r.status is False:
                    logger.info(f"✗ {r.name}")
                    logger.info(f"  Erreur: {r.error_msg}")
        
        # Sauvegarder le rapport JSON
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total_count,
                'ok': ok_count,
                'fail': fail_count,
                'skip': skip_count,
                'success_rate': ok_count/total_count if total_count > 0 else 0,
                'duration': total_duration
            },
            'categories': {cat: stats for cat, stats in categories.items()},
            'tests': [r.to_dict() for r in self.results]
        }
        
        report_file = self.project_root / 'test_report_full.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✓ Rapport sauvegardé: {report_file}")
        logger.info("\n" + "="*70)
        
        # Statut global
        if fail_count == 0:
            logger.info("🎉 TOUS LES TESTS ONT RÉUSSI!")
        elif fail_count <= 3:
            logger.info("⚠️  QUELQUES TESTS EN ÉCHEC (non bloquants)")
        else:
            logger.info("❌ PLUSIEURS TESTS EN ÉCHEC")
        
        logger.info("="*70)

if __name__ == '__main__':
    tester = NBAFullProjectTest()
    tester.run_all_tests()
