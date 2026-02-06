#!/usr/bin/env python3
"""
Orchestrateur NBA-15: Recuperation complete des donnees matchs et equipes
Coordonne tous les modules avec checkpoints et progression
"""

import logging
import sys
from datetime import datetime
from typing import Dict, Any

# Ajouter src au path
sys.path.insert(0, '.')

from src.utils.checkpoint_manager import CheckpointManager
from src.utils.progress_tracker import ProgressTracker
from src.ingestion.fetch_teams_rosters import fetch_teams_and_rosters
from src.ingestion.fetch_schedules import fetch_all_schedules
from src.ingestion.fetch_team_stats import fetch_all_team_stats
from src.ingestion.fetch_boxscores import fetch_and_partition_boxscores

logger = logging.getLogger(__name__)

SEASON = "2023-24"


class NBA15Orchestrator:
    """Orchestre l'execution complete de NBA-15"""
    
    def __init__(self):
        self.checkpoint = CheckpointManager()
        self.progress = None
        self.results = {}
        
    def run(self, resume: bool = True) -> Dict[str, Any]:
        """
        Execute l'orchestration complete
        
        Args:
            resume: Si True, reprend depuis le dernier checkpoint
        
        Returns:
            Resultats de toutes les etapes
        """
        logger.info("="*70)
        logger.info("[NBA-15] ORCHESTRATEUR COMPLET")
        logger.info("="*70)
        logger.info(f"[SEASON] Saison: {SEASON}")
        logger.info(f"[RESTART] Reprise: {'Oui' if resume else 'Non (from scratch)'}")
        logger.info("="*70)
        
        # Initialiser le tracker de progression
        self.progress = ProgressTracker(total_steps=5, desc="NBA-15")
        
        # Si pas de reprise, reset
        if not resume:
            self.checkpoint.reset()
            logger.info("[RESTART] Checkpoint reinitialise")
        
        # Verifier point de reprise
        resume_point = self.checkpoint.get_resume_point()
        if resume_point:
            logger.info(f"[CHECKPOINT] Point de reprise: {resume_point}")
        
        try:
            # Etape 1: Equipes et Rosters
            if not self.checkpoint.is_step_completed("teams_rosters"):
                self._run_step("teams_rosters", self._fetch_teams_rosters)
            else:
                logger.info("[OK] Etape deja completee - SKIP")
                self.progress.complete_step()
            
            # Etape 2: Stats Equipes
            if not self.checkpoint.is_step_completed("team_stats"):
                self._run_step("team_stats", self._fetch_team_stats)
            else:
                logger.info("[OK] Etape 'team_stats' deja completee - SKIP")
                self.progress.complete_step()
            
            # Etape 3: Calendriers
            if not self.checkpoint.is_step_completed("schedules"):
                self._run_step("schedules", self._fetch_schedules)
            else:
                logger.info("[OK] Etape 'schedules' deja completee - SKIP")
                self.progress.complete_step()
            
            # Etape 4: Box Scores
            if not self.checkpoint.is_step_completed("boxscores"):
                self._run_step("boxscores", self._fetch_boxscores)
            else:
                logger.info("[OK] Etape 'boxscores' deja completee - SKIP")
                self.progress.complete_step()
            
            # Etape 5: Validation
            if not self.checkpoint.is_step_completed("validation"):
                self._run_step("validation", self._validate_data)
            else:
                logger.info("[OK] Etape 'validation' deja completee - SKIP")
                self.progress.complete_step()
            
            # Finalisation
            self._finalize()
            
        except Exception as e:
            logger.error(f"[ERROR] ERREUR FATALE: {e}")
            logger.error("Le checkpoint a ete sauvegarde. Relancez pour reprendre.")
            raise
        
        finally:
            if self.progress:
                self.progress.close()
        
        return self.results
    
    def _run_step(self, step_name: str, step_func):
        """Execute une etape avec gestion d'erreur"""
        logger.info(f"{'='*70}")
        logger.info(f"[STEP] ETAPE: {step_name.upper()}")
        logger.info(f"{'='*70}")
        
        # Marquer le debut
        self.checkpoint.start_step(step_name)
        self.progress.start_step(step_name)
        
        try:
            # Executer l'etape
            result = step_func()
            self.results[step_name] = result
            
            # Marquer comme complete
            self.checkpoint.complete_step(step_name, result)
            
            # Mettre a jour la progression
            items_count = result.get('stats', {}).get('total_players', 0) if isinstance(result, dict) else 0
            self.progress.complete_step(items_count=items_count)
            
            logger.info(f"[OK] Etape '{step_name}' terminee avec succes")
            
        except Exception as e:
            logger.error(f"[ERROR] Etape '{step_name}' echouee: {e}")
            raise
    
    def _fetch_teams_rosters(self) -> Dict:
        """Recupere les equipes et rosters"""
        return fetch_teams_and_rosters()
    
    def _fetch_team_stats(self) -> Dict:
        """Recupere les stats collectives"""
        return fetch_all_team_stats()
    
    def _fetch_schedules(self) -> Dict:
        """Recupere les calendriers"""
        return fetch_all_schedules()
    
    def _fetch_boxscores(self) -> Dict:
        """Recupere les box scores"""
        return fetch_and_partition_boxscores()
    
    def _validate_data(self) -> Dict:
        """Valide les donnees recuperees"""
        logger.info("[SEARCH] Validation des donnees...")
        
        # TODO: Implementer validation complete
        # Pour l'instant, juste verifier que les fichiers existent
        import os
        
        required_files = [
            f"data/raw/teams/teams_{SEASON.replace('-', '_')}.json",
            f"data/raw/rosters/roster_{SEASON.replace('-', '_')}.json",
            f"data/raw/teams_stats/team_stats_{SEASON.replace('-', '_')}.json",
            f"data/raw/schedules/schedule_{SEASON.replace('-', '_')}.json",
        ]
        
        validation_results = {
            'files_checked': [],
            'files_missing': [],
            'is_valid': True
        }
        
        for filepath in required_files:
            if os.path.exists(filepath):
                validation_results['files_checked'].append(filepath)
                logger.info(f"[OK] {filepath}")
            else:
                validation_results['files_missing'].append(filepath)
                validation_results['is_valid'] = False
                logger.error(f"[ERROR] Fichier manquant: {filepath}")
        
        # Verifier box scores
        boxscores_dir = "data/raw/games_boxscores"
        if os.path.exists(boxscores_dir):
            files = os.listdir(boxscores_dir)
            logger.info(f"[OK] {len(files)} fichiers box scores trouves")
            validation_results['boxscores_count'] = len(files)
        else:
            logger.error(f"[ERROR] Repertoire box scores manquant: {boxscores_dir}")
            validation_results['is_valid'] = False
        
        return validation_results
    
    def _finalize(self):
        """Finalise l'execution"""
        logger.info("\n" + "="*70)
        logger.info("[OK] NBA-15 TERMINE AVEC SUCCÈS")
        logger.info("="*70)
        
        # Afficher resume
        stats = self.checkpoint.get_progress_stats()
        logger.info(f"[STATS] Progression: {stats['completed']}/{stats['total']} etapes")
        logger.info(f"[STATS] Pourcentage: {stats['percentage']:.1f}%")
        
        # Afficher temps total
        if self.progress:
            elapsed = self.progress.get_elapsed()
            logger.info(f"[TIME] Temps total: {elapsed}")
        
        # Liste des fichiers crees
        logger.info("\n[DIR] Fichiers crees:")
        files = [
            f"data/raw/teams/teams_{SEASON.replace('-', '_')}.json",
            f"data/raw/rosters/roster_{SEASON.replace('-', '_')}.json",
            f"data/raw/teams_stats/team_stats_{SEASON.replace('-', '_')}.json",
            f"data/raw/schedules/schedule_{SEASON.replace('-', '_')}.json",
            f"data/raw/games_boxscores/*_games.json"
        ]
        for f in files:
            logger.info(f"   - {f}")
        
        logger.info("="*70)


def main():
    """Point d'entree principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NBA-15: Recuperation donnees matchs et equipes')
    parser.add_argument('--from-scratch', action='store_true', 
                        help='Recommencer depuis le debut (ignore checkpoints)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Mode verbose (plus de logs)')
    
    args = parser.parse_args()
    
    # Configuration logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Executer
    orchestrator = NBA15Orchestrator()
    
    try:
        results = orchestrator.run(resume=not args.from_scratch)
        print("\n[OK] Execution terminee avec succes!")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Erreur: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
