#!/usr/bin/env python3
"""
Pipeline Full Season - Predictions pour toute la saison 2025-26
Hérite de DailyPredictionPipeline pour zero redondance

Usage:
    # Générer prédictions pour toute la saison
    python src/ml/pipeline/full_season_pipeline.py --predict-full
    
    # Mise à jour quotidienne (appelé par cron à 9h)
    python src/ml/pipeline/full_season_pipeline.py --daily-update
    
    # Vérifier alertes
    python src/ml/pipeline/full_season_pipeline.py --check-alerts
"""

import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

import pandas as pd
import numpy as np
import joblib

# Ajouter les paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # Racine projet
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from nba.config import SeasonConfig, settings
from daily_pipeline import DailyPredictionPipeline

# Import des alertes existantes
try:
    from src.utils.alerts import alert_on_performance_degradation
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False
    logging.warning("Alert system not available")

# Import API NBA
try:
    from nba_api.stats.endpoints import leaguegamefinder
    from nba_api.live.nba.endpoints import scoreboard
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    logging.warning("NBA API not available")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullSeasonPipeline(DailyPredictionPipeline):
    """
    Pipeline complet pour la saison 2025-26
    Hérite de DailyPredictionPipeline pour réutiliser le code existant
    """
    
    def __init__(self, season: str = None):
        """
        Initialize pipeline
        
        Args:
            season: Saison cible (default: SeasonConfig.CURRENT_SEASON)
        """
        super().__init__()
        self.season = season or SeasonConfig.CURRENT_SEASON
        self.predictions_file = settings.predictions_path / f"season_{self.season}_full.json"
        self.tracking_file = settings.predictions_path / "tracking_history.csv"
        self.comparison_file = settings.predictions_path / "daily_comparison.json"
        
        # S'assurer que le répertoire existe
        settings.predictions_path.mkdir(parents=True, exist_ok=True)
        
        # Chargement du meilleur modèle (optimized)
        self._use_optimized_model()
        
        logger.info(f"FullSeasonPipeline initialisé pour saison {self.season}")
        logger.info(f"Modèle utilisé: {self.model_path}")
    
    def _use_optimized_model(self):
        """Configure pour utiliser le modèle optimisé (meilleur performance)"""
        self.model_path = settings.model_xgb_path  # models/optimized/model_xgb.joblib
        self.calibrator_path = settings.calibrator_xgb_path
        self.selected_features_path = settings.selected_features_path
        
        # Charger features sélectionnées
        if self.selected_features_path.exists():
            with open(self.selected_features_path, 'r') as f:
                features_data = json.load(f)
                self.selected_features = features_data.get('features', [])
            logger.info(f"Features sélectionnées: {len(self.selected_features)}")
        else:
            self.selected_features = None
            logger.warning("Fichier features sélectionnées non trouvé")
    
    def load_resources(self):
        """Charge toutes les ressources nécessaires avec le modèle optimisé"""
        logger.info("Chargement des ressources (modèle optimisé)...")
        
        # 1. Modèle XGB optimisé
        self.model = joblib.load(self.model_path)
        logger.info(f"[OK] Modèle XGB optimisé chargé: {self.model_path}")
        
        # 2. Calibrateur (si disponible)
        if Path(self.calibrator_path).exists():
            self.calibrator = joblib.load(self.calibrator_path)
            logger.info("[OK] Calibrateur chargé")
        else:
            self.calibrator = None
            logger.warning("Calibrateur non trouvé")
        
        # 3. Données historiques
        self.historical_data = pd.read_parquet(settings.features_v3_path)
        logger.info("[OK] Données historiques chargées")
        
        # 4. Mapping équipes
        with open(settings.team_mapping_path, 'r') as f:
            self.team_name_to_id = json.load(f)
        logger.info("[OK] Mapping équipes chargé")
        
        # 5. Features (utiliser uniquement les features sélectionnées si disponible)
        if self.selected_features:
            self.features_cols = self.selected_features
            logger.info(f"[OK] {len(self.features_cols)} features sélectionnées chargées")
        else:
            # Fallback: calculer comme avant
            exclude_cols = [
                'game_id', 'season', 'game_date', 'season_type',
                'home_team_id', 'away_team_id', 'target',
                'home_score', 'away_score', 'point_diff'
            ]
            self.features_cols = [c for c in self.historical_data.columns if c not in exclude_cols]
            logger.info(f"[OK] {len(self.features_cols)} features disponibles (fallback)")
    
    def predict_match(self, home_team: str, away_team: str):
        """
        Predire un match avec calibration des probabilités
        """
        features = self.engineer_features_for_match(home_team, away_team)
        
        if features is None:
            return {
                'home_team': home_team,
                'away_team': away_team,
                'error': 'Donnees historiques insuffisantes'
            }
        
        # Prédiction brute
        proba_raw = self.model.predict_proba(features)[0, 1]
        
        # Calibration (si disponible)
        if self.calibrator:
            proba = self.calibrator.predict_proba(features)[0, 1]
            logger.debug(f"Calibration: {proba_raw:.3f} -> {proba:.3f}")
        else:
            proba = proba_raw
        
        prediction = 1 if proba > 0.5 else 0
        confidence = max(proba, 1 - proba)
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'prediction': 'Home Win' if prediction == 1 else 'Away Win',
            'proba_home_win': float(proba),
            'confidence': float(confidence),
            'recommendation': self._get_recommendation(confidence)
        }
    
    def fetch_season_schedule(self) -> List[Dict]:
        """
        Récupère le calendrier complet avec matchs futurs via scheduleleaguev2
        
        Returns:
            Liste des matchs avec indicateur is_played
        """
        try:
            # Utiliser la nouvelle fonction fetch_future_schedule
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'ingestion'))
            from fetch_schedules import fetch_future_schedule
            
            games = fetch_future_schedule(self.season)
            
            if games:
                logger.info(f"Calendrier complet récupéré: {len(games)} matchs")
                played = sum(1 for g in games if g.get('is_played'))
                future = len(games) - played
                logger.info(f"  - Matchs joués: {played}")
                logger.info(f"  - Matchs à venir: {future}")
            
            return games
            
        except Exception as e:
            logger.error(f"Erreur récupération calendrier: {e}")
            # Fallback sur ancienne méthode
            return self._fetch_season_schedule_legacy()
    
    def fetch_season_schedule(self) -> List[Dict]:
        """
        Récupère le calendrier complet de la saison via NBA API
        
        Returns:
            Liste des matchs de la saison
        """
        if not NBA_API_AVAILABLE:
            logger.error("NBA API non disponible")
            return []
        
        logger.info(f"Récupération du calendrier {self.season}...")
        
        try:
            from nba_api.stats.endpoints import leaguegamefinder
            
            # Regular Season
            games_rs = leaguegamefinder.LeagueGameFinder(
                season_nullable=self.season,
                season_type_nullable="Regular Season",
                league_id_nullable="00"
            )
            
            games_data = games_rs.get_normalized_dict()
            games_list = games_data.get('LeagueGameFinderResults', [])
            
            # Formater les matchs
            formatted_games = []
            for game in games_list:
                formatted_games.append({
                    'game_id': game.get('GAME_ID'),
                    'game_date': game.get('GAME_DATE'),
                    'season': self.season,
                    'season_type': 'Regular Season',
                    'team_id': game.get('TEAM_ID'),
                    'team_name': game.get('TEAM_NAME'),
                    'team_abbreviation': game.get('TEAM_ABBREVIATION'),
                    'matchup': game.get('MATCHUP'),
                    'wl': game.get('WL'),
                    'points': game.get('PTS'),
                    'home_team': None,  # À extraire du matchup
                    'away_team': None,
                    'is_played': game.get('WL') is not None  # Si WL existe, match joué
                })
            
            # Grouper par game_id pour créer des matchs complets
            games_by_id = {}
            for game in formatted_games:
                gid = game['game_id']
                if gid not in games_by_id:
                    games_by_id[gid] = []
                games_by_id[gid].append(game)
            
            # Créer les matchs complets (home vs away)
            complete_games = []
            for gid, teams in games_by_id.items():
                if len(teams) == 2:
                    home_team = None
                    away_team = None
                    
                    for team in teams:
                        matchup = team.get('matchup', '')
                        if 'vs.' in matchup:
                            home_team = team
                        elif '@' in matchup:
                            away_team = team
                    
                    if home_team and away_team:
                        complete_games.append({
                            'game_id': gid,
                            'game_date': home_team['game_date'],
                            'season': self.season,
                            'home_team': home_team['team_name'],
                            'away_team': away_team['team_name'],
                            'home_score': home_team.get('points'),
                            'away_score': away_team.get('points'),
                            'is_played': home_team.get('is_played', False),
                            'winner': 'HOME' if home_team.get('wl') == 'W' else 'AWAY' if away_team.get('wl') == 'W' else None
                        })
            
            # Trier par date
            complete_games.sort(key=lambda x: x['game_date'])
            
            logger.info(f"{len(complete_games)} matchs récupérés")
            return complete_games
            
        except Exception as e:
            logger.error(f"Erreur récupération calendrier: {e}")
            return []
    
    def predict_full_season(self) -> Dict[str, Any]:
        """
        Génère les prédictions pour tous les matchs non-joués de la saison
        
        Returns:
            Dictionnaire avec toutes les prédictions
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"GENERATION DES PREDICTIONS SAISON {self.season}")
        logger.info(f"{'='*70}\n")
        
        # 1. Charger les ressources
        self.load_resources()
        
        # 2. Récupérer le calendrier
        schedule = self.fetch_season_schedule()
        
        if not schedule:
            logger.error("Impossible de récupérer le calendrier")
            return {}
        
        # 3. Séparer matchs joués et non-joués
        today = datetime.now().strftime('%Y-%m-%d')
        
        games_played = [g for g in schedule if g.get('is_played')]
        games_future = [g for g in schedule if not g.get('is_played') and g['game_date'] >= today]
        
        logger.info(f"Matchs déjà joués: {len(games_played)}")
        logger.info(f"Matchs à venir: {len(games_future)}")
        
        # 4. Générer prédictions pour les matchs futurs
        predictions = []
        
        for i, game in enumerate(games_future, 1):
            logger.info(f"[{i}/{len(games_future)}] {game['home_team']} vs {game['away_team']}")
            
            pred = self.predict_match(game['home_team'], game['away_team'])
            
            prediction_record = {
                'game_id': game['game_id'],
                'game_date': game['game_date'],
                'season': self.season,
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'predicted_winner': pred.get('prediction'),
                'confidence': pred.get('confidence'),
                'proba_home_win': pred.get('proba_home_win'),
                'recommendation': pred.get('recommendation'),
                'actual_winner': None,  # Sera rempli après le match
                'is_correct': None,     # Sera rempli après le match
                'status': 'PREDICTED',
                'predicted_at': datetime.now().isoformat()
            }
            
            predictions.append(prediction_record)
            
            if 'error' in pred:
                logger.warning(f"  -> ERREUR: {pred['error']}")
            else:
                logger.info(f"  -> {pred['prediction']} (confiance: {pred['confidence']:.2%})")
        
        # 5. Créer le document de sortie
        output = {
            'season': self.season,
            'generated_at': datetime.now().isoformat(),
            'total_games': len(schedule),
            'games_played': len(games_played),
            'games_future': len(games_future),
            'predictions': predictions
        }
        
        # 6. Sauvegarder
        self._save_full_season_predictions(output)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"PREDICTIONS GENEREES: {len(predictions)} matchs")
        logger.info(f"Fichier: {self.predictions_file}")
        logger.info(f"{'='*70}\n")
        
        return output
    
    def _save_full_season_predictions(self, predictions: Dict):
        """Sauvegarde les prédictions complètes"""
        with open(self.predictions_file, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, indent=2, ensure_ascii=False)
        logger.info(f"Prédictions sauvegardées: {self.predictions_file}")
    
    def auto_update_results(self) -> Dict[str, Any]:
        """
        Récupère les résultats réels du jour précédent et compare avec les prédictions
        À exécuter quotidiennement par cron à 9h
        
        Returns:
            Résumé des mises à jour
        """
        logger.info(f"\n{'='*70}")
        logger.info("MISE A JOUR QUOTIDIENNE DES RESULTATS")
        logger.info(f"{'='*70}\n")
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 1. Charger les prédictions existantes
        if not self.predictions_file.exists():
            logger.error(f"Fichier de prédictions non trouvé: {self.predictions_file}")
            return {'error': 'No predictions file'}
        
        with open(self.predictions_file, 'r') as f:
            season_data = json.load(f)
        
        predictions = season_data.get('predictions', [])
        
        # 2. Récupérer les résultats d'hier via API
        results_yesterday = self._fetch_yesterday_results(yesterday)
        
        if not results_yesterday:
            logger.info(f"Aucun résultat trouvé pour {yesterday}")
            return {'updated': 0, 'date': yesterday}
        
        # 3. Mettre à jour les prédictions avec les résultats réels
        updated_count = 0
        daily_accuracy = []
        
        for result in results_yesterday:
            home_team = result['home_team']
            away_team = result['away_team']
            actual_winner = result['winner']  # 'HOME' ou 'AWAY'
            
            # Trouver la prédiction correspondante
            for pred in predictions:
                if (pred['home_team'] == home_team and 
                    pred['away_team'] == away_team and
                    pred['game_date'] == yesterday):
                    
                    # Mettre à jour
                    pred['actual_winner'] = actual_winner
                    pred['status'] = 'COMPLETED'
                    pred['updated_at'] = datetime.now().isoformat()
                    
                    # Vérifier si correct
                    predicted_winner = 'HOME' if pred['predicted_winner'] == 'Home Win' else 'AWAY'
                    is_correct = predicted_winner == actual_winner
                    pred['is_correct'] = is_correct
                    
                    updated_count += 1
                    daily_accuracy.append(is_correct)
                    
                    logger.info(f"{home_team} vs {away_team}: "
                              f"Prédit={predicted_winner}, "
                              f"Réel={actual_winner}, "
                              f"{'✓' if is_correct else '✗'}")
                    break
        
        # 4. Calculer l'accuracy du jour
        if daily_accuracy:
            accuracy = sum(daily_accuracy) / len(daily_accuracy)
            logger.info(f"\nAccuracy du {yesterday}: {accuracy:.2%} ({sum(daily_accuracy)}/{len(daily_accuracy)})")
        else:
            accuracy = None
        
        # 5. Sauvegarder les mises à jour
        season_data['predictions'] = predictions
        season_data['last_updated'] = datetime.now().isoformat()
        self._save_full_season_predictions(season_data)
        
        # 6. Mettre à jour l'historique de tracking
        self._update_tracking_history(yesterday, updated_count, accuracy, daily_accuracy)
        
        result = {
            'date': yesterday,
            'updated': updated_count,
            'accuracy': accuracy,
            'total_games': len(daily_accuracy)
        }
        
        logger.info(f"\n{'='*70}")
        logger.info(f"MISE A JOUR TERMINEE: {updated_count} matchs")
        logger.info(f"{'='*70}\n")
        
        return result
    
    def _fetch_yesterday_results(self, date_str: str) -> List[Dict]:
        """
        Récupère les résultats des matchs d'une date spécifique
        
        Args:
            date_str: Date au format 'YYYY-MM-DD'
            
        Returns:
            Liste des résultats
        """
        if not NBA_API_AVAILABLE:
            logger.error("NBA API non disponible")
            return []
        
        try:
            from nba_api.stats.endpoints import leaguegamefinder
            
            games = leaguegamefinder.LeagueGameFinder(
                date_from_nullable=date_str,
                date_to_nullable=date_str,
                league_id_nullable="00"
            )
            
            games_data = games.get_normalized_dict()
            games_list = games_data.get('LeagueGameFinderResults', [])
            
            # Grouper par game_id
            games_by_id = {}
            for game in games_list:
                gid = game.get('GAME_ID')
                if gid not in games_by_id:
                    games_by_id[gid] = []
                games_by_id[gid].append(game)
            
            # Créer les résultats complets
            results = []
            for gid, teams in games_by_id.items():
                if len(teams) == 2:
                    home_team = None
                    away_team = None
                    
                    for team in teams:
                        matchup = team.get('MATCHUP', '')
                        if 'vs.' in matchup:
                            home_team = team
                        elif '@' in matchup:
                            away_team = team
                    
                    if home_team and away_team:
                        winner = 'HOME' if home_team.get('WL') == 'W' else 'AWAY'
                        results.append({
                            'game_id': gid,
                            'date': date_str,
                            'home_team': home_team.get('TEAM_NAME'),
                            'away_team': away_team.get('TEAM_NAME'),
                            'home_score': home_team.get('PTS'),
                            'away_score': away_team.get('PTS'),
                            'winner': winner
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur récupération résultats: {e}")
            return []
    
    def _update_tracking_history(self, date: str, games_count: int, 
                                 accuracy: float, results: List[bool]):
        """Met à jour le fichier d'historique des performances"""
        import csv
        
        file_exists = self.tracking_file.exists()
        
        with open(self.tracking_file, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['date', 'games', 'correct', 'accuracy', 'season'])
            
            if accuracy is not None:
                correct = sum(results)
                writer.writerow([date, games_count, correct, f"{accuracy:.4f}", self.season])
            else:
                writer.writerow([date, games_count, 0, 0.0, self.season])
        
        logger.info(f"Historique mis à jour: {self.tracking_file}")
    
    def check_performance_alerts(self) -> Dict[str, Any]:
        """
        Vérifie si des alertes sont nécessaires basées sur les performances
        Seuil: accuracy < 60% sur les 7 derniers jours
        
        Returns:
            Statut des alertes
        """
        logger.info(f"\n{'='*70}")
        logger.info("VERIFICATION DES ALERTES DE PERFORMANCE")
        logger.info(f"{'='*70}\n")
        
        # 1. Charger l'historique
        if not self.tracking_file.exists():
            logger.warning("Aucun historique trouvé")
            return {'alerts': [], 'status': 'no_data'}
        
        history = pd.read_csv(self.tracking_file)
        
        # 2. Calculer accuracy sur les 7 derniers jours avec données
        recent = history[history['season'] == self.season].tail(7)
        
        if len(recent) == 0:
            logger.info("Pas assez d'historique pour les alertes")
            return {'alerts': [], 'status': 'insufficient_data'}
        
        # Calculer accuracy moyenne pondérée
        total_games = recent['games'].sum()
        total_correct = recent['correct'].sum()
        
        if total_games > 0:
            accuracy_7d = total_correct / total_games
        else:
            accuracy_7d = 0.0
        
        logger.info(f"Accuracy 7 derniers jours: {accuracy_7d:.2%}")
        logger.info(f"Matchs analysés: {total_games}")
        
        # 3. Vérifier les seuils
        alerts = []
        
        if accuracy_7d < 0.60:
            alert_msg = f"ALERTE: Accuracy faible sur 7 jours ({accuracy_7d:.2%})"
            alerts.append({
                'type': 'performance',
                'severity': 'high',
                'message': alert_msg,
                'threshold': 0.60,
                'actual': accuracy_7d,
                'date': datetime.now().isoformat()
            })
            logger.warning(alert_msg)
            
            # Envoyer alerte via système existant
            if ALERTS_AVAILABLE:
                alert_on_performance_degradation(
                    metric_name="7-day accuracy",
                    current_value=accuracy_7d,
                    threshold=0.60
                )
        
        if accuracy_7d < 0.58:
            alert_msg = f"RETRAIN RECOMMANDE: Accuracy critique ({accuracy_7d:.2%})"
            alerts.append({
                'type': 'retrain_needed',
                'severity': 'critical',
                'message': alert_msg,
                'threshold': 0.58,
                'actual': accuracy_7d
            })
            logger.error(alert_msg)
        
        # 4. Sauvegarder les alertes
        if alerts:
            self._save_alerts(alerts)
        
        result = {
            'alerts': alerts,
            'accuracy_7d': accuracy_7d,
            'games_analyzed': total_games,
            'status': 'alert' if alerts else 'ok'
        }
        
        logger.info(f"\n{'='*70}")
        logger.info(f"VERIFICATION TERMINEE: {len(alerts)} alerte(s)")
        logger.info(f"{'='*70}\n")
        
        return result
    
    def _save_alerts(self, alerts: List[Dict]):
        """Sauvegarde les alertes dans un fichier log"""
        alerts_file = settings.predictions_path / "alert_history.log"
        
        with open(alerts_file, 'a') as f:
            for alert in alerts:
                f.write(f"{datetime.now().isoformat()} - {alert['type'].upper()} - {alert['message']}\n")
        
        logger.info(f"Alertes sauvegardées: {alerts_file}")
    
    def get_season_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé de la saison en cours
        
        Returns:
            Résumé avec stats globales
        """
        if not self.predictions_file.exists():
            return {'error': 'No predictions file'}
        
        with open(self.predictions_file, 'r') as f:
            data = json.load(f)
        
        predictions = data.get('predictions', [])
        
        # Statistiques
        total = len(predictions)
        played = [p for p in predictions if p.get('status') == 'COMPLETED']
        correct = [p for p in played if p.get('is_correct')]
        
        overall_accuracy = len(correct) / len(played) if played else 0.0
        
        return {
            'season': self.season,
            'total_games': total,
            'games_played': len(played),
            'games_remaining': total - len(played),
            'correct_predictions': len(correct),
            'overall_accuracy': overall_accuracy,
            'generated_at': data.get('generated_at')
        }


def main():
    """Point d'entrée CLI"""
    parser = argparse.ArgumentParser(description='Pipeline Full Season NBA')
    parser.add_argument('--predict-full', action='store_true',
                       help='Générer prédictions pour toute la saison')
    parser.add_argument('--daily-update', action='store_true',
                       help='Mise à jour quotidienne (cron 9h)')
    parser.add_argument('--check-alerts', action='store_true',
                       help='Vérifier les alertes de performance')
    parser.add_argument('--summary', action='store_true',
                       help='Afficher résumé de la saison')
    parser.add_argument('--season', type=str, default=None,
                       help='Saison cible (default: 2025-26)')
    
    args = parser.parse_args()
    
    # Initialiser pipeline
    pipeline = FullSeasonPipeline(season=args.season)
    
    if args.predict_full:
        pipeline.predict_full_season()
    elif args.daily_update:
        pipeline.auto_update_results()
        pipeline.check_performance_alerts()
    elif args.check_alerts:
        pipeline.check_performance_alerts()
    elif args.summary:
        summary = pipeline.get_season_summary()
        print(json.dumps(summary, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
