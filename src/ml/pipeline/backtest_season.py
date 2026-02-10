#!/usr/bin/env python3
"""
Backtesting Réaliste - Saison NBA 2025-26
Approche sans data leakage - simulation jour par jour

Usage:
    from backtest_season import SeasonBacktester
    backtester = SeasonBacktester()
    results = backtester.run_backtest(include_playoffs=True)
"""

import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss

# Ajouter les paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from nba.config import SeasonConfig, settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Recalcule les features sans data leakage
    Utilise uniquement l'historique avant la date de prédiction
    """
    
    def __init__(self):
        self.team_history = defaultdict(list)  # Historique par équipe
        self.h2h_history = defaultdict(list)   # Historique head-to-head
        
    def add_game_result(self, game: Dict):
        """Ajoute un match à l'historique après sa prédiction"""
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Stocker pour l'équipe home
        self.team_history[home_team].append({
            'date': game['game_date'],
            'is_home': True,
            'won': game['home_score'] > game['away_score'],
            'score': game['home_score'],
            'opp_score': game['away_score'],
            'point_diff': game['home_score'] - game['away_score']
        })
        
        # Stocker pour l'équipe away
        self.team_history[away_team].append({
            'date': game['game_date'],
            'is_home': False,
            'won': game['away_score'] > game['home_score'],
            'score': game['away_score'],
            'opp_score': game['home_score'],
            'point_diff': game['away_score'] - game['home_score']
        })
        
        # Stocker H2H
        h2h_key = tuple(sorted([home_team, away_team]))
        self.h2h_history[h2h_key].append({
            'date': game['game_date'],
            'home_team': home_team,
            'home_won': game['home_score'] > game['away_score'],
            'point_diff': game['home_score'] - game['away_score']
        })
    
    def calculate_team_features(self, team: str, current_date: str) -> Dict:
        """Calcule les features d'une équipe jusqu'à current_date (exclus)"""
        games = [g for g in self.team_history[team] if g['date'] < current_date]
        
        if not games:
            return None
        
        # Derniers matchs
        last_5 = games[-5:] if len(games) >= 5 else games
        last_10 = games[-10:] if len(games) >= 10 else games
        
        # Win percentages
        win_pct = sum(1 for g in games if g['won']) / len(games)
        win_pct_last_5 = sum(1 for g in last_5 if g['won']) / len(last_5)
        win_pct_last_10 = sum(1 for g in last_10 if g['won']) / len(last_10)
        
        # Points moyens
        avg_pts = np.mean([g['score'] for g in games])
        avg_pts_last_5 = np.mean([g['score'] for g in last_5])
        
        # Momentum (tendance récente)
        if len(games) >= 10:
            recent_wins = sum(1 for g in last_5 if g['won'])
            older_wins = sum(1 for g in games[-10:-5] if g['won'])
            momentum = (recent_wins / 5) - (older_wins / 5)
        else:
            momentum = 0
        
        # Consistency (écart-type des différentiels de points)
        point_diffs = [g['point_diff'] for g in games]
        consistency = np.std(point_diffs) if len(point_diffs) > 1 else 0
        
        # Form vs average
        form_vs_avg = avg_pts_last_5 - avg_pts if len(games) >= 5 else 0
        
        return {
            'win_pct': win_pct,
            'wins_last_10': sum(1 for g in last_10 if g['won']),
            'avg_pts': avg_pts,
            'avg_pts_last_5': avg_pts_last_5,
            'momentum': momentum,
            'consistency': consistency,
            'form_vs_avg': form_vs_avg,
            'games_played': len(games)
        }
    
    def calculate_h2h_features(self, home_team: str, away_team: str, current_date: str) -> Dict:
        """Calcule les features head-to-head"""
        h2h_key = tuple(sorted([home_team, away_team]))
        h2h_games = [g for g in self.h2h_history[h2h_key] if g['date'] < current_date]
        
        if not h2h_games:
            return {
                'h2h_games': 0,
                'h2h_home_wins': 0,
                'h2h_home_win_rate': 0.5,
                'h2h_avg_margin': 0
            }
        
        # Home wins in H2H
        home_wins = sum(1 for g in h2h_games if g['home_won'])
        
        # Margins
        margins = [g['point_diff'] for g in h2h_games]
        
        return {
            'h2h_games': len(h2h_games),
            'h2h_home_wins': home_wins,
            'h2h_home_win_rate': home_wins / len(h2h_games),
            'h2h_avg_margin': np.mean(margins)
        }
    
    def engineer_features(self, home_team: str, away_team: str, current_date: str) -> Optional[pd.DataFrame]:
        """Crée le vecteur de features complet"""
        # Features home team
        home_features = self.calculate_team_features(home_team, current_date)
        if home_features is None:
            return None
        
        # Features away team
        away_features = self.calculate_team_features(away_team, current_date)
        if away_features is None:
            return None
        
        # Features H2H
        h2h_features = self.calculate_h2h_features(home_team, away_team, current_date)
        
        # Combiner en features différentielles
        features = {
            # Win percentages
            'win_pct_diff': home_features['win_pct'] - away_features['win_pct'],
            'win_pct_diff_squared': (home_features['win_pct'] - away_features['win_pct']) ** 2,
            
            # Wins last 10
            'home_wins_last_10': home_features['wins_last_10'],
            'away_wins_last_10': away_features['wins_last_10'],
            
            # Points
            'pts_diff_last_5': home_features['avg_pts_last_5'] - away_features['avg_pts_last_5'],
            
            # Momentum
            'home_momentum': home_features['momentum'],
            'away_momentum': away_features['momentum'],
            'momentum_diff_v3': home_features['momentum'] - away_features['momentum'],
            
            # Consistency
            'home_consistency': home_features['consistency'],
            'away_consistency': away_features['consistency'],
            'consistency_diff': home_features['consistency'] - away_features['consistency'],
            
            # Form
            'home_weighted_form': home_features['form_vs_avg'],
            'away_weighted_form': away_features['form_vs_avg'],
            'weighted_form_diff': home_features['form_vs_avg'] - away_features['form_vs_avg'],
            
            # H2H
            'h2h_games': h2h_features['h2h_games'],
            'h2h_home_wins': h2h_features['h2h_home_wins'],
            'h2h_home_win_rate': h2h_features['h2h_home_win_rate'],
            'h2h_avg_margin': h2h_features['h2h_avg_margin'],
            'h2h_margin_squared': h2h_features['h2h_avg_margin'] ** 2,
            
            # Features supplémentaires simulées
            'home_rest_days': 2,  # Valeur par défaut
            'away_rest_days': 2,
            'rest_advantage': 0,
            'home_advantage': 0.1,
            'momentum_acceleration': 0,
            'trend_diff': home_features['momentum'] - away_features['momentum'],
            'clutch_diff': 0,
            'off_eff_diff': 0,
            'rest_form_interaction': 0,
            'fatigue_impact': 0,
            'home_short_vs_long': 0,
            'away_short_vs_long': 0,
            'home_trend': home_features['momentum'],
            'away_trend': away_features['momentum'],
            'h2h_weighted': h2h_features['h2h_home_win_rate']
        }
        
        return pd.DataFrame([features])


class SeasonBacktester:
    """
    Backtesting réaliste d'une saison NBA
    Sans data leakage - simulation jour par jour
    """
    
    def __init__(self, season: str = None):
        self.season = season or SeasonConfig.CURRENT_SEASON
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.calibrator = None
        self.predictions = []
        
        # Charger le modèle
        self._load_model()
        
    def _load_model(self):
        """Charge le modèle optimisé"""
        try:
            self.model = joblib.load(settings.model_xgb_path)
            logger.info(f"Modèle chargé: {settings.model_xgb_path}")
            
            if Path(settings.calibrator_xgb_path).exists():
                self.calibrator = joblib.load(settings.calibrator_xgb_path)
                logger.info("Calibrateur chargé")
        except Exception as e:
            logger.error(f"Erreur chargement modèle: {e}")
            raise
    
    def fetch_season_games(self, include_playoffs: bool = True) -> List[Dict]:
        """Récupère tous les matchs de la saison avec résultats"""
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'ingestion'))
            from fetch_schedules import fetch_season_schedule
            
            games = []
            
            # Regular Season
            rs_games = fetch_season_schedule(self.season, "Regular Season")
            games.extend(rs_games)
            logger.info(f"Regular Season: {len(rs_games)} matchs")
            
            # Playoffs (si demandé)
            if include_playoffs:
                try:
                    po_games = fetch_season_schedule(self.season, "Playoffs")
                    games.extend(po_games)
                    logger.info(f"Playoffs: {len(po_games)} matchs")
                except:
                    logger.info("Pas de playoffs disponibles")
            
            # Grouper par game_id
            games_by_id = defaultdict(list)
            for game in games:
                games_by_id[game['game_id']].append(game)
            
            # Créer matchs complets
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
                            'home_team_id': home_team['team_id'],
                            'away_team_id': away_team['team_id'],
                            'home_score': home_team.get('points'),
                            'away_score': away_team.get('points'),
                            'actual_winner': 'HOME' if home_team.get('wl') == 'W' else 'AWAY',
                            'is_played': True
                        })
            
            # Trier par date
            complete_games.sort(key=lambda x: x['game_date'])
            
            logger.info(f"Total matchs complets: {len(complete_games)}")
            return complete_games
            
        except Exception as e:
            logger.error(f"Erreur récupération matchs: {e}")
            return []
    
    def run_backtest(self, include_playoffs: bool = True, max_games: int = None) -> Dict:
        """
        Exécute le backtest jour par jour
        
        Args:
            include_playoffs: Inclure les playoffs
            max_games: Limiter le nombre de matchs (pour tests)
        
        Returns:
            Résultats complets du backtest
        """
        logger.info("\n" + "="*70)
        logger.info(f"BACKTEST SAISON {self.season}")
        logger.info("="*70)
        logger.info(f"Approche: Réaliste (sans data leakage)")
        logger.info(f"Include playoffs: {include_playoffs}")
        logger.info("="*70 + "\n")
        
        # 1. Récupérer les matchs
        games = self.fetch_season_games(include_playoffs)
        
        if max_games:
            games = games[:max_games]
            logger.info(f"Limité à {max_games} matchs pour le test")
        
        if not games:
            logger.error("Aucun match trouvé")
            return {}
        
        # 2. Initialiser l'historique avec des données de la saison précédente
        # (pour avoir des features dès le premier match)
        self._initialize_history()
        
        # 3. Simuler jour par jour
        predictions = []
        current_date = None
        daily_games = []
        
        for i, game in enumerate(games, 1):
            # Nouveau jour ?
            if game['game_date'] != current_date:
                # Traiter les matchs du jour précédent
                if daily_games:
                    self._process_day_results(daily_games)
                
                current_date = game['game_date']
                daily_games = []
                
                if i % 50 == 0:
                    logger.info(f"[{i}/{len(games)}] Date: {current_date}")
            
            # Prédire ce match
            pred = self._predict_game(game)
            if pred:
                predictions.append(pred)
            
            daily_games.append(game)
        
        # Traiter le dernier jour
        if daily_games:
            self._process_day_results(daily_games)
        
        # 4. Calculer les métriques
        results = self._calculate_metrics(predictions, games)
        
        # 5. Sauvegarder
        self._save_results(results)
        
        logger.info("\n" + "="*70)
        logger.info("BACKTEST TERMINÉ")
        logger.info("="*70)
        logger.info(f"Total matchs analysés: {len(predictions)}")
        logger.info(f"Accuracy: {results['summary']['accuracy']:.2%}")
        logger.info("="*70 + "\n")
        
        return results
    
    def _initialize_history(self):
        """Initialise l'historique avec des matchs de la saison précédente"""
        try:
            # Charger les features existantes pour avoir un historique de départ
            df = pd.read_parquet(settings.features_v3_path)
            
            # Filtrer pour les matchs avant la saison courante
            prev_season = f"{int(self.season.split('-')[0]) - 1}-{self.season.split('-')[1]}"
            prev_games = df[df['season'] == prev_season]
            
            if len(prev_games) > 0:
                logger.info(f"Initialisation avec {len(prev_games)} matchs de la saison {prev_season}")
                
                # Ajouter ces matchs à l'historique
                for _, game in prev_games.iterrows():
                    self.feature_engineer.add_game_result({
                        'game_date': str(game['game_date']),
                        'home_team': f"Team_{game['home_team_id']}",  # Simplifié
                        'away_team': f"Team_{game['away_team_id']}",
                        'home_score': game['home_score'],
                        'away_score': game['away_score']
                    })
        except Exception as e:
            logger.warning(f"Impossible d'initialiser l'historique: {e}")
    
    def _predict_game(self, game: Dict) -> Optional[Dict]:
        """Prédit un match spécifique"""
        try:
            # Debug: vérifier le type du modèle
            if not hasattr(self.model, 'predict_proba'):
                logger.error(f"DEBUG: self.model type = {type(self.model)}")
                logger.error(f"DEBUG: self.model value = {self.model}")
                return None
            
            # Créer les features (sans data leakage)
            features = self.feature_engineer.engineer_features(
                game['home_team'],
                game['away_team'],
                game['game_date']
            )
            
            if features is None:
                return None
            
            # Vérifier que toutes les features nécessaires sont présentes
            # Charger les features attendues
            try:
                with open(settings.selected_features_path, 'r') as f:
                    features_data = json.load(f)
                    if isinstance(features_data, dict):
                        expected_features = features_data.get('features', [])
                    elif isinstance(features_data, list):
                        expected_features = features_data
                    else:
                        expected_features = []
                        logger.warning(f"Format inattendu pour selected_features: {type(features_data)}")
            except Exception as e:
                logger.error(f"Erreur chargement features: {e}")
                expected_features = []
            
            # Ajouter les features manquantes avec valeur 0
            for feat in expected_features:
                if feat not in features.columns:
                    features[feat] = 0
            
            # Réordonner
            features = features[expected_features]
            
            # Prédire
            proba_raw = self.model.predict_proba(features)[0, 1]
            
            # Calibrer
            if self.calibrator:
                proba = self.calibrator.predict_proba(features)[0, 1]
            else:
                proba = proba_raw
            
            prediction = 1 if proba > 0.5 else 0
            predicted_winner = 'Home Win' if prediction == 1 else 'Away Win'
            confidence = max(proba, 1 - proba)
            
            # Vérifier si correct
            is_correct = (predicted_winner == 'Home Win' and game['actual_winner'] == 'HOME') or \
                        (predicted_winner == 'Away Win' and game['actual_winner'] == 'AWAY')
            
            return {
                'game_id': game['game_id'],
                'game_date': game['game_date'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'predicted_winner': predicted_winner,
                'proba_home_win': float(proba),
                'confidence': float(confidence),
                'actual_winner': game['actual_winner'],
                'is_correct': is_correct,
                'home_score': game['home_score'],
                'away_score': game['away_score']
            }
            
        except Exception as e:
            logger.warning(f"Erreur prédiction {game['game_id']}: {e}")
            return None
    
    def _process_day_results(self, games: List[Dict]):
        """Ajoute les résultats du jour à l'historique"""
        for game in games:
            self.feature_engineer.add_game_result(game)
    
    def _calculate_metrics(self, predictions: List[Dict], all_games: List[Dict]) -> Dict:
        """Calcule toutes les métriques de performance"""
        if not predictions:
            return {}
        
        # Convertir en arrays
        y_true = [1 if p['actual_winner'] == 'HOME' else 0 for p in predictions]
        y_pred = [1 if p['predicted_winner'] == 'Home Win' else 0 for p in predictions]
        y_proba = [p['proba_home_win'] for p in predictions]
        
        # Métriques globales
        metrics = {
            'total_games': len(predictions),
            'total_scheduled': len(all_games),
            'coverage': len(predictions) / len(all_games),
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
            'auc': roc_auc_score(y_true, y_proba) if len(set(y_true)) > 1 else 0.5,
            'brier_score': brier_score_loss(y_true, y_proba)
        }
        
        # Par mois
        by_month = defaultdict(lambda: {'games': 0, 'correct': 0})
        for p in predictions:
            month = p['game_date'][:7]  # YYYY-MM
            by_month[month]['games'] += 1
            if p['is_correct']:
                by_month[month]['correct'] += 1
        
        by_month_metrics = {}
        for month, stats in by_month.items():
            by_month_metrics[month] = {
                'games': stats['games'],
                'correct': stats['correct'],
                'accuracy': stats['correct'] / stats['games'] if stats['games'] > 0 else 0
            }
        
        # Par équipe
        by_team = defaultdict(lambda: {'predicted': 0, 'correct': 0})
        for p in predictions:
            for team in [p['home_team'], p['away_team']]:
                by_team[team]['predicted'] += 1
                if p['is_correct']:
                    by_team[team]['correct'] += 1
        
        by_team_metrics = {}
        for team, stats in by_team.items():
            by_team_metrics[team] = {
                'predicted': stats['predicted'],
                'correct': stats['correct'],
                'accuracy': stats['correct'] / stats['predicted'] if stats['predicted'] > 0 else 0
            }
        
        # Par niveau de confiance
        by_confidence = {
            'HIGH': {'games': 0, 'correct': 0},
            'MEDIUM': {'games': 0, 'correct': 0},
            'LOW': {'games': 0, 'correct': 0}
        }
        
        for p in predictions:
            conf = p['confidence']
            if conf >= 0.70:
                level = 'HIGH'
            elif conf >= 0.60:
                level = 'MEDIUM'
            else:
                level = 'LOW'
            
            by_confidence[level]['games'] += 1
            if p['is_correct']:
                by_confidence[level]['correct'] += 1
        
        by_confidence_metrics = {}
        for level, stats in by_confidence.items():
            by_confidence_metrics[level] = {
                'games': stats['games'],
                'correct': stats['correct'],
                'accuracy': stats['correct'] / stats['games'] if stats['games'] > 0 else 0
            }
        
        return {
            'summary': metrics,
            'by_month': by_month_metrics,
            'by_team': by_team_metrics,
            'by_confidence': by_confidence_metrics,
            'predictions': predictions
        }
    
    def _save_results(self, results: Dict):
        """Sauvegarde les résultats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON complet
        json_path = settings.predictions_path / f"backtest_{self.season}_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Résultats sauvegardés: {json_path}")
        
        # CSV des prédictions
        csv_path = settings.predictions_path / f"backtest_{self.season}_{timestamp}.csv"
        df = pd.DataFrame(results['predictions'])
        df.to_csv(csv_path, index=False)
        logger.info(f"CSV sauvegardé: {csv_path}")
        
        # Résumé simple
        summary_path = settings.predictions_path / f"backtest_summary_{self.season}.txt"
        with open(summary_path, 'w') as f:
            f.write(f"BACKTEST SAISON {self.season}\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total matchs: {results['summary']['total_games']}\n")
            f.write(f"Accuracy: {results['summary']['accuracy']:.2%}\n")
            f.write(f"Precision: {results['summary']['precision']:.2%}\n")
            f.write(f"Recall: {results['summary']['recall']:.2%}\n")
            f.write(f"F1-Score: {results['summary']['f1']:.2%}\n")
            f.write(f"AUC: {results['summary']['auc']:.4f}\n")
            f.write(f"Brier Score: {results['summary']['brier_score']:.4f}\n")


if __name__ == "__main__":
    # Test rapide
    backtester = SeasonBacktester()
    results = backtester.run_backtest(include_playoffs=True, max_games=50)
    print(f"\nAccuracy: {results['summary']['accuracy']:.2%}")
