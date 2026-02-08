"""
NBA-22: Pipeline d'Entraînement des Modèles ML

Entraîne et évalue Random Forest et Gradient Boosting pour prédiction matchs NBA.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NBA22Trainer:
    """
    Pipeline complet d'entraînement NBA-22.
    
    Charge les features NBA-21, split temporel, entraîne RF + GBT,
    évalue et sauvegarde le meilleur modèle.
    """
    
    def __init__(self, features_path: str = "data/gold/ml_features/features_all.parquet"):
        self.features_path = Path(features_path)
        self.df = None
        self.feature_cols = []
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.models = {}
        self.results = {}
        
    def load_data(self) -> pd.DataFrame:
        """Charge les features NBA-21 depuis Parquet."""
        logger.info(f"Chargement des features depuis {self.features_path}")
        
        if not self.features_path.exists():
            raise FileNotFoundError(f"Features non trouvées: {self.features_path}")
        
        self.df = pd.read_parquet(self.features_path)
        
        # Convertir game_date en datetime
        self.df['game_date'] = pd.to_datetime(self.df['game_date'])
        
        # Identifier les colonnes features
        # EXCLURE: target, métadonnées, ET toute info post-match (data leakage!)
        # 
        # ⚠️ CRITIQUE: Seules les features disponibles AVANT le match sont valides:
        # - Stats historiques (avg_last_5/10/20)
        # - Contexte (rest_days, back_to_back)
        # - Win rates cumulés (win_pct, wins_last_10)
        # - H2H historique
        # - Tendances historiques
        #
        # ❌ EXCLURE TOUTE MÉTRIQUE CALCULÉE SUR LE MATCH EN COURS:
        # - Scores, rebonds, passes du match
        # - TS%, eFG%, Game Score (calculés sur le match)
        exclude_cols = [
            # IDs et métadonnées
            'game_id', 'season', 'game_date', 'season_type',
            'home_team_id', 'home_team_name', 'home_team_abbr',
            'away_team_id', 'away_team_name', 'away_team_abbr',
            'home_wl', 'away_wl', 'target',
            # ⚠️ DATA LEAKAGE: scores et stats du match en cours
            'point_diff', 'home_score', 'away_score',
            'home_reb', 'home_ast', 'home_stl', 'home_blk', 'home_tov', 'home_pf',
            'away_reb', 'away_ast', 'away_stl', 'away_blk', 'away_tov', 'away_pf',
            # ⚠️ DATA LEAKAGE: métriques avancées du match en cours
            'home_ts_pct', 'home_efg_pct', 'home_game_score', 'home_fatigue_eff',
            'away_ts_pct', 'away_efg_pct', 'away_game_score', 'away_fatigue_eff',
            'ts_pct_diff'  # Calculé à partir de ts_pct
        ]
        
        self.feature_cols = [c for c in self.df.columns if c not in exclude_cols]
        
        logger.info(f"Features utilisées ({len(self.feature_cols)}):")
        for i, col in enumerate(self.feature_cols, 1):
            logger.info(f"  {i:2d}. {col}")
        
        logger.info(f"Données chargées: {len(self.df)} matchs, {len(self.feature_cols)} features")
        logger.info(f"Saisons: {sorted(self.df['season'].unique())}")
        
        return self.df
    
    def temporal_split(self, test_seasons: List[str] = None) -> Tuple:
        """
        Split temporel des données (pas de shuffle !).
        
        Par défaut: train sur 2018-2022, test sur 2023-2025
        """
        if test_seasons is None:
            test_seasons = ['2023-24', '2024-25']
        
        logger.info(f"Split temporel - Test seasons: {test_seasons}")
        
        # Split par saison
        train_mask = ~self.df['season'].isin(test_seasons)
        test_mask = self.df['season'].isin(test_seasons)
        
        self.X_train = self.df.loc[train_mask, self.feature_cols].copy()
        self.X_test = self.df.loc[test_mask, self.feature_cols].copy()
        self.y_train = self.df.loc[train_mask, 'target'].copy()
        self.y_test = self.df.loc[test_mask, 'target'].copy()
        
        logger.info(f"Train: {len(self.X_train)} matchs ({self.y_train.mean():.1%} home wins)")
        logger.info(f"Test: {len(self.X_test)} matchs ({self.y_test.mean():.1%} home wins)")
        
        # Vérifier qu'on a pas de fuite de données
        train_dates = self.df.loc[train_mask, 'game_date'].max()
        test_dates = self.df.loc[test_mask, 'game_date'].min()
        logger.info(f"Dernière date train: {train_dates}")
        logger.info(f"Première date test: {test_dates}")
        
        if train_dates >= test_dates:
            logger.warning("⚠️ RISQUE DE FUITE DE DONNÉES TEMPORIELLE!")
        else:
            logger.info("✅ Pas de fuite de données temporelle")
        
        return (self.X_train, self.X_test, self.y_train, self.y_test)
    
    def train_random_forest(self) -> Dict:
        """Entraîne Random Forest (baseline)."""
        logger.info("\n" + "="*70)
        logger.info("ENTRAÎNEMENT RANDOM FOREST")
        logger.info("="*70)
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(self.X_train, self.y_train)
        
        # Predictions
        y_pred = model.predict(self.X_test)
        y_proba = model.predict_proba(self.X_test)[:, 1]
        
        # Métriques
        metrics = self._calculate_metrics(self.y_test, y_pred, y_proba)
        metrics['model_name'] = 'Random Forest'
        metrics['algorithm'] = 'rf'
        
        # Feature importance
        feature_importance = dict(zip(
            self.feature_cols,
            model.feature_importances_
        ))
        feature_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        metrics['feature_importance'] = feature_importance
        
        self.models['rf'] = model
        self.results['rf'] = metrics
        
        logger.info(f"✅ Random Forest - Accuracy: {metrics['accuracy']:.3f}")
        
        return metrics
    
    def train_gradient_boosting(self) -> Dict:
        """Entraîne Gradient Boosting (optimisé)."""
        logger.info("\n" + "="*70)
        logger.info("ENTRAÎNEMENT GRADIENT BOOSTING")
        logger.info("="*70)
        
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        model.fit(self.X_train, self.y_train)
        
        # Predictions
        y_pred = model.predict(self.X_test)
        y_proba = model.predict_proba(self.X_test)[:, 1]
        
        # Métriques
        metrics = self._calculate_metrics(self.y_test, y_pred, y_proba)
        metrics['model_name'] = 'Gradient Boosting'
        metrics['algorithm'] = 'gbt'
        
        # Feature importance
        feature_importance = dict(zip(
            self.feature_cols,
            model.feature_importances_
        ))
        feature_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        metrics['feature_importance'] = feature_importance
        
        self.models['gbt'] = model
        self.results['gbt'] = metrics
        
        logger.info(f"✅ Gradient Boosting - Accuracy: {metrics['accuracy']:.3f}")
        
        return metrics
    
    def _calculate_metrics(self, y_true, y_pred, y_proba) -> Dict:
        """Calcule toutes les métriques de classification."""
        return {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, zero_division=0)),
            'f1': float(f1_score(y_true, y_pred, zero_division=0)),
            'auc': float(roc_auc_score(y_true, y_proba)),
            'n_train': len(self.y_train),
            'n_test': len(y_true),
            'home_win_rate_test': float(y_true.mean()),
            'home_win_rate_pred': float(y_pred.mean())
        }
    
    def cross_validate_rf(self, n_splits: int = 5) -> Dict:
        """
        Validation croisée temporelle pour Random Forest.
        
        Utilise TimeSeriesSplit pour respecter l'ordre temporel.
        """
        logger.info("\n" + "="*70)
        logger.info(f"VALIDATION CROISÉE TEMPORELLE ({n_splits} splits)")
        logger.info("="*70)
        
        # Trier par date
        df_sorted = self.df.sort_values('game_date')
        X = df_sorted[self.feature_cols]
        y = df_sorted['target']
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        cv_scores = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
            X_train_cv, X_test_cv = X.iloc[train_idx], X.iloc[test_idx]
            y_train_cv, y_test_cv = y.iloc[train_idx], y.iloc[test_idx]
            
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train_cv, y_train_cv)
            
            acc = accuracy_score(y_test_cv, model.predict(X_test_cv))
            cv_scores.append(acc)
            
            logger.info(f"Fold {fold}: Accuracy = {acc:.3f} ({len(test_idx)} matchs)")
        
        cv_results = {
            'cv_mean': float(np.mean(cv_scores)),
            'cv_std': float(np.std(cv_scores)),
            'cv_scores': [float(s) for s in cv_scores]
        }
        
        logger.info(f"CV Mean: {cv_results['cv_mean']:.3f} (+/- {cv_results['cv_std']*2:.3f})")
        
        return cv_results
    
    def save_models(self, output_dir: str = None) -> str:
        """
        Sauvegarde les modèles entraînés.
        
        Returns:
            Chemin du dossier d'expérimentation créé
        """
        # Créer dossier expérimentation avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_dir is None:
            output_dir = Path("models/experiments") / f"nba22_{timestamp}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\nSauvegarde des modèles dans {output_dir}")
        
        # Sauvegarder chaque modèle
        for name, model in self.models.items():
            model_path = output_dir / f"model_{name}.joblib"
            joblib.dump(model, model_path)
            logger.info(f"  ✅ Modèle {name.upper()}: {model_path}")
        
        # Sauvegarder les résultats comparatifs
        comparison = {
            'timestamp': timestamp,
            'models': self.results,
            'best_model': self._get_best_model(),
            'feature_cols': self.feature_cols,
            'n_features': len(self.feature_cols),
            'train_size': len(self.X_train),
            'test_size': len(self.X_test)
        }
        
        metrics_path = output_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        logger.info(f"  ✅ Métriques: {metrics_path}")
        
        return str(output_dir)
    
    def _get_best_model(self) -> Dict:
        """Identifie le meilleur modèle selon l'accuracy."""
        best = max(self.results.items(), key=lambda x: x[1]['accuracy'])
        return {
            'name': best[0],
            'accuracy': best[1]['accuracy'],
            'algorithm': best[1]['algorithm']
        }
    
    def print_results(self):
        """Affiche le tableau comparatif des résultats."""
        logger.info("\n" + "="*70)
        logger.info("RÉSULTATS COMPARATIFS")
        logger.info("="*70)
        
        for name, metrics in self.results.items():
            logger.info(f"\n{metrics['model_name']}:")
            logger.info(f"  Accuracy:  {metrics['accuracy']:.3f}")
            logger.info(f"  Precision: {metrics['precision']:.3f}")
            logger.info(f"  Recall:    {metrics['recall']:.3f}")
            logger.info(f"  F1-Score:  {metrics['f1']:.3f}")
            logger.info(f"  AUC:       {metrics['auc']:.3f}")
            logger.info(f"  Top feature: {list(metrics['feature_importance'].keys())[0]}")
        
        best = self._get_best_model()
        logger.info(f"\n🏆 MEILLEUR MODÈLE: {best['name'].upper()}")
        logger.info(f"   Accuracy: {best['accuracy']:.3f}")
        
        # Vérifier objectif > 60%
        if best['accuracy'] > 0.60:
            logger.info("   ✅ Objectif atteint (> 60%)")
        else:
            logger.info("   ❌ Objectif non atteint (< 60%)")
    
    def run(self, save: bool = True) -> Dict:
        """
        Pipeline complet NBA-22.
        
        Returns:
            Dict avec les résultats des deux modèles
        """
        logger.info("="*70)
        logger.info("NBA-22: PIPELINE D'ENTRAÎNEMENT ML")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        # 1. Chargement
        self.load_data()
        
        # 2. Split temporel
        self.temporal_split()
        
        # 3. Entraînement RF
        self.train_random_forest()
        
        # 4. Entraînement GBT
        self.train_gradient_boosting()
        
        # 5. Résultats
        self.print_results()
        
        # 6. Sauvegarde
        output_dir = None
        if save:
            output_dir = self.save_models()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n{'='*70}")
        logger.info(f"Pipeline terminé en {elapsed:.1f}s")
        logger.info(f"{'='*70}")
        
        return {
            'results': self.results,
            'best_model': self._get_best_model(),
            'output_dir': output_dir,
            'elapsed_seconds': elapsed
        }


def main():
    """Point d'entrée pour exécution directe."""
    trainer = NBA22Trainer()
    results = trainer.run(save=True)
    return results


if __name__ == "__main__":
    main()
