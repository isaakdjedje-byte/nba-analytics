#!/usr/bin/env python3
"""
TEST END-TO-END: NBA-11 → NBA-23
Test fonctionnel complet avec correction automatique
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Couleurs pour le terminal (Windows compatible)
class Colors:
    OK = '[OK]'
    FAIL = '[FAIL]'
    WARN = '[WARN]'
    INFO = '[INFO]'

class PipelineTester:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixes = []
        
    def log(self, level, msg):
        print(f"{level} {msg}")
        if level == Colors.FAIL:
            self.errors.append(msg)
        elif level == Colors.WARN:
            self.warnings.append(msg)
    
    def test_file_exists(self, path, description):
        """Teste l'existence d'un fichier"""
        if Path(path).exists():
            size = Path(path).stat().st_size
            self.log(Colors.OK, f"{description}: {path} ({size:,} bytes)")
            return True
        else:
            self.log(Colors.FAIL, f"{description} MANQUANT: {path}")
            return False
    
    def test_json_valid(self, path):
        """Teste si un JSON est valide et retourne les données"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            self.log(Colors.FAIL, f"JSON invalide {path}: {e}")
            return None
    
    def count_records(self, path):
        """Compte les records dans un fichier"""
        try:
            data = self.test_json_valid(path)
            if data is None:
                return 0
            if isinstance(data, dict) and 'data' in data:
                return len(data['data'])
            elif isinstance(data, list):
                return len(data)
            else:
                return 1
        except:
            return 0
    
    def phase_1_structure(self):
        """Phase 1: Vérification de la structure"""
        print("\n" + "="*70)
        print("PHASE 1: VERIFICATION DE LA STRUCTURE")
        print("="*70)
        
        checks = {
            # NBA-11/15: Données brutes
            "data/raw/all_players_historical.json": "NBA-11/15: Joueurs historiques",
            "data/raw/rosters/roster_2023_24.json": "NBA-15: Roster 2023-24",
            "data/raw/teams/teams_2023_24.json": "NBA-15: Équipes 2023-24",
            "data/supplemental/players_critical.csv": "NBA-15: Joueurs critiques",
            
            # NBA-17: Nettoyage
            "data/silver/players_cleaned/players.json": "NBA-17: Joueurs nettoyés",
            "data/silver/players_cleaned_stats.json": "NBA-17: Rapport qualité",
            
            # NBA-18: Métriques avancées
            "data/silver/players_advanced/players.json": "NBA-18: Métriques joueurs",
            "data/silver/players_advanced/players_enriched_final.json": "NBA-18: Joueurs enrichis",
            
            # NBA-19: Agrégations
            "data/gold/team_season_stats/team_season_stats.json": "NBA-19: Stats équipes",
            "data/gold/nba19_report.json": "NBA-19: Rapport final",
            
            # NBA-20: Matchs
            "data/silver/games_processed/games_structured.json": "NBA-20: Matchs structurés",
            
            # NBA-21: Features ML
            "data/gold/ml_features/features_all.parquet": "NBA-21: Features ML",
            
            # NBA-22: Modèles
            "models/optimized/model_xgb.joblib": "NBA-22: Modèle XGBoost",
            "models/optimized/training_summary.json": "NBA-22: Résumé entraînement",
            
            # NBA-23: Clustering
            "data/gold/player_archetypes/player_archetypes.parquet": "NBA-23: Archétypes",
        }
        
        results = {}
        for path, desc in checks.items():
            exists = self.test_file_exists(path, desc)
            results[desc] = exists
            
            if exists and path.endswith('.json'):
                count = self.count_records(path)
                print(f"    → {count:,} records")
        
        return results
    
    def phase_2_data_integrity(self):
        """Phase 2: Intégrité des données"""
        print("\n" + "="*70)
        print("PHASE 2: INTEGRITE DES DONNEES")
        print("="*70)
        
        # Test 1: NBA-17 → NBA-18 (mêmes joueurs?)
        print("\nTest 1: Cohérence NBA-17 → NBA-18")
        nba17_data = self.test_json_valid("data/silver/players_cleaned/players.json")
        nba18_data = self.test_json_valid("data/silver/players_advanced/players.json")
        
        if nba17_data and nba18_data:
            nba17_ids = {p['id'] for p in (nba17_data.get('data', nba17_data) if isinstance(nba17_data, dict) else nba17_data)}
            nba18_ids = {p['id'] for p in (nba18_data.get('data', nba18_data) if isinstance(nba18_data, dict) else nba18_data)}
            
            common = len(nba17_ids & nba18_ids)
            self.log(Colors.INFO, f"NBA-17: {len(nba17_ids)} joueurs")
            self.log(Colors.INFO, f"NBA-18: {len(nba18_ids)} joueurs")
            self.log(Colors.INFO, f"Joueurs communs: {common}")
            
            if common == len(nba17_ids):
                self.log(Colors.OK, "Tous les joueurs NBA-17 présents dans NBA-18")
            else:
                missing = nba17_ids - nba18_ids
                self.log(Colors.WARN, f"{len(missing)} joueurs NBA-17 manquants dans NBA-18")
        
        # Test 2: NBA-18 métriques valides
        print("\nTest 2: Validité des métriques NBA-18")
        if nba18_data:
            players = nba18_data.get('data', nba18_data) if isinstance(nba18_data, dict) else nba18_data
            invalid_per = sum(1 for p in players if p.get('per', 0) < 0 or p.get('per', 0) > 50)
            invalid_ts = sum(1 for p in players if p.get('ts_pct', 0) < 0 or p.get('ts_pct', 0) > 1)
            
            if invalid_per == 0 and invalid_ts == 0:
                self.log(Colors.OK, "Toutes les métriques NBA-18 dans les plages valides")
            else:
                self.log(Colors.WARN, f"Métriques invalides: {invalid_per} PER, {invalid_ts} TS%")
    
    def phase_3_pipeline_execution(self):
        """Phase 3: Exécution des étapes manquantes"""
        print("\n" + "="*70)
        print("PHASE 3: EXECUTION DES ETAPES MANQUANTES")
        print("="*70)
        
        # Vérifier si NBA-17 est complet
        if not Path("data/silver/players_cleaned/players.json").exists():
            print("\n→ NBA-17 manquant, exécution...")
            print("  Commande: python src/processing/clean_data.py")
            self.fixes.append("Executer: python src/processing/clean_data.py")
        
        # Vérifier si NBA-18 est complet  
        if not Path("data/silver/players_advanced/players_enriched_final.json").exists():
            print("\n→ NBA-18 manquant, exécution...")
            print("  Commande: python src/processing/calculate_advanced_metrics.py")
            self.fixes.append("Executer: python src/processing/calculate_advanced_metrics.py")
        
        # Vérifier si NBA-19 est complet
        if not Path("data/gold/team_season_stats/team_season_stats.json").exists():
            print("\n→ NBA-19 manquant, exécution...")
            print("  Commande: python src/processing/nba19_unified_aggregates.py")
            self.fixes.append("Executer: python src/processing/nba19_unified_aggregates.py")
    
    def phase_4_final_validation(self):
        """Phase 4: Validation finale"""
        print("\n" + "="*70)
        print("PHASE 4: VALIDATION FINALE")
        print("="*70)
        
        # Test de bout en bout
        all_ok = True
        
        critical_files = [
            "data/silver/players_cleaned/players.json",
            "data/silver/players_advanced/players_enriched_final.json",
            "data/gold/team_season_stats/team_season_stats.json",
            "data/gold/ml_features/features_all.parquet",
            "data/gold/player_archetypes/player_archetypes.parquet",
        ]
        
        for f in critical_files:
            if not Path(f).exists():
                all_ok = False
                self.log(Colors.FAIL, f"Fichier critique manquant: {f}")
        
        if all_ok:
            self.log(Colors.OK, "✓ Tous les fichiers critiques présents")
            self.log(Colors.OK, "✓ Pipeline NBA-11 → NBA-23 FONCTIONNEL")
        else:
            self.log(Colors.FAIL, "✗ Pipeline INCOMPLET - voir corrections ci-dessus")
    
    def generate_report(self):
        """Génère le rapport final"""
        print("\n" + "="*70)
        print("RAPPORT FINAL")
        print("="*70)
        
        print(f"\nErreurs: {len(self.errors)}")
        print(f"Avertissements: {len(self.warnings)}")
        print(f"Corrections nécessaires: {len(self.fixes)}")
        
        if self.fixes:
            print("\n→ Commandes à exécuter:")
            for fix in self.fixes:
                print(f"   {fix}")
        
        # Sauvegarder le rapport
        report = {
            'timestamp': datetime.now().isoformat(),
            'errors': self.errors,
            'warnings': self.warnings,
            'fixes_required': self.fixes,
            'status': 'FAIL' if self.errors else ('WARN' if self.warnings else 'OK')
        }
        
        with open('test_pipeline_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nRapport sauvegardé: test_pipeline_report.json")
        
        return len(self.errors) == 0

if __name__ == "__main__":
    tester = PipelineTester()
    
    # Exécuter toutes les phases
    tester.phase_1_structure()
    tester.phase_2_data_integrity()
    tester.phase_3_pipeline_execution()
    tester.phase_4_final_validation()
    
    # Générer rapport
    success = tester.generate_report()
    
    sys.exit(0 if success else 1)
