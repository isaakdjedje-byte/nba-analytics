"""
NBA-22 Optimization: Feature Selection Module
Sélectionne les features optimales pour réduire de 80 à 30-40
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from sklearn.feature_selection import (
    SelectKBest, f_classif, mutual_info_classif, 
    RFE, SelectFromModel
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
import xgboost as xgb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeatureSelector:
    """
    Sélectionne les meilleures features parmi les 80 disponibles.
    
    Objectif: Réduire de 80 à 30-40 features pour:
    - Réduire l'overfitting
    - Améliorer la vitesse d'inférence
    - Garder seulement les features significatives
    
    Méthodes:
    - Filter: ANOVA F-test, Mutual Information
    - Wrapper: Recursive Feature Elimination (RFE)
    - Embedded: Feature importance from XGBoost/RF
    """
    
    def __init__(self, n_features=35):
        self.n_features = n_features
        self.selected_features = None
        self.feature_scores = {}
        self.selector = None
        
    def load_data(self, features_path, exclude_cols=None):
        """Charge les données features."""
        logger.info(f"Chargement des features depuis {features_path}")
        
        df = pd.read_parquet(features_path)
        df['game_date'] = pd.to_datetime(df['game_date'])
        df = df.sort_values('game_date')
        
        if exclude_cols is None:
            exclude_cols = [
                'game_id', 'season', 'game_date', 'season_type',
                'home_team_id', 'away_team_id', 'target',
                'home_score', 'away_score', 'point_diff',
                'home_reb', 'home_ast', 'home_stl', 'home_blk', 'home_tov', 'home_pf',
                'away_reb', 'away_ast', 'away_stl', 'away_blk', 'away_tov', 'away_pf',
                'home_ts_pct', 'home_efg_pct', 'home_game_score', 'home_fatigue_eff',
                'away_ts_pct', 'away_efg_pct', 'away_game_score', 'away_fatigue_eff',
                'ts_pct_diff'
            ]
        
        self.feature_cols = [c for c in df.columns if c not in exclude_cols]
        self.df = df
        
        logger.info(f"Données chargées: {len(df)} matchs, {len(self.feature_cols)} features")
        return df
    
    def split_temporal(self, test_seasons=None):
        """Split temporel des données."""
        if test_seasons is None:
            test_seasons = ['2023-24', '2024-25']
        
        train_mask = ~self.df['season'].isin(test_seasons)
        test_mask = self.df['season'].isin(test_seasons)
        
        self.X_train = self.df.loc[train_mask, self.feature_cols].copy()
        self.X_test = self.df.loc[test_mask, self.feature_cols].copy()
        self.y_train = self.df.loc[train_mask, 'target'].copy()
        self.y_test = self.df.loc[test_mask, 'target'].copy()
        
        logger.info(f"Train: {len(self.X_train)} matchs, Test: {len(self.X_test)} matchs")
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def select_anova_f(self):
        """Sélection par ANOVA F-test."""
        logger.info("\n" + "="*70)
        logger.info("SELECTION: ANOVA F-TEST")
        logger.info("="*70)
        
        selector = SelectKBest(score_func=f_classif, k=self.n_features)
        selector.fit(self.X_train, self.y_train)
        
        # Scores
        scores = pd.Series(selector.scores_, index=self.feature_cols).sort_values(ascending=False)
        selected = self.X_train.columns[selector.get_support()].tolist()
        
        self.selected_features = selected
        self.feature_scores['anova_f'] = scores.to_dict()
        
        logger.info(f"Top 5 features ANOVA F:")
        for feat, score in scores.head(5).items():
            logger.info(f"  {feat}: {score:.2f}")
        
        return selected, scores
    
    def select_mutual_info(self):
        """Sélection par Mutual Information."""
        logger.info("\n" + "="*70)
        logger.info("SELECTION: MUTUAL INFORMATION")
        logger.info("="*70)
        
        selector = SelectKBest(score_func=mutual_info_classif, k=self.n_features)
        selector.fit(self.X_train, self.y_train)
        
        scores = pd.Series(selector.scores_, index=self.feature_cols).sort_values(ascending=False)
        selected = self.X_train.columns[selector.get_support()].tolist()
        
        self.selected_features = selected
        self.feature_scores['mutual_info'] = scores.to_dict()
        
        logger.info(f"Top 5 features Mutual Info:")
        for feat, score in scores.head(5).items():
            logger.info(f"  {feat}: {score:.4f}")
        
        return selected, scores
    
    def select_rfe_xgb(self):
        """Sélection par Recursive Feature Elimination avec XGBoost."""
        logger.info("\n" + "="*70)
        logger.info("SELECTION: RFE avec XGBoost")
        logger.info("="*70)
        
        # XGBoost pour RFE
        estimator = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        
        selector = RFE(estimator=estimator, n_features_to_select=self.n_features, step=0.1)
        selector.fit(self.X_train, self.y_train)
        
        selected = self.X_train.columns[selector.support_].tolist()
        rankings = pd.Series(selector.ranking_, index=self.feature_cols).sort_values()
        
        self.feature_scores['rfe_xgb'] = rankings.to_dict()
        
        logger.info(f"Top 5 features RFE (ranking=1):")
        for feat in selected[:5]:
            logger.info(f"  {feat}")
        
        return selected, rankings
    
    def select_xgb_importance(self):
        """Sélection par importance des features XGBoost."""
        logger.info("\n" + "="*70)
        logger.info("SELECTION: XGBoost Feature Importance")
        logger.info("="*70)
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        model.fit(self.X_train, self.y_train)
        
        importance = pd.Series(model.feature_importances_, index=self.feature_cols)
        importance = importance.sort_values(ascending=False)
        
        selected = importance.head(self.n_features).index.tolist()
        self.selected_features = selected
        self.feature_scores['xgb_importance'] = importance.to_dict()
        
        logger.info(f"Top 5 features XGB Importance:")
        for feat, imp in importance.head(5).items():
            logger.info(f"  {feat}: {imp:.4f}")
        
        return selected, importance
    
    def ensemble_selection(self, methods=None, weights=None):
        """
        Combine plusieurs méthodes de sélection.
        
        Chaque feature reçoit un score basé sur son rang dans chaque méthode.
        """
        logger.info("\n" + "="*70)
        logger.info("SELECTION: ENSEMBLE (Combinaison des méthodes)")
        logger.info("="*70)
        
        if methods is None:
            # Exécuter toutes les méthodes
            methods = {}
            methods['anova_f'] = self.select_anova_f()[1]
            methods['mutual_info'] = self.select_mutual_info()[1]
            methods['xgb_importance'] = self.select_xgb_importance()[1]
        
        if weights is None:
            weights = {'anova_f': 0.25, 'mutual_info': 0.25, 'xgb_importance': 0.5}
        
        # Normaliser les scores (0-1)
        normalized_scores = {}
        for method, scores in methods.items():
            if isinstance(scores, pd.Series):
                min_val = scores.min()
                max_val = scores.max()
                if max_val > min_val:
                    normalized_scores[method] = (scores - min_val) / (max_val - min_val)
                else:
                    normalized_scores[method] = scores
            else:
                # Si c'est un dict
                s = pd.Series(scores)
                min_val = s.min()
                max_val = s.max()
                if max_val > min_val:
                    normalized_scores[method] = (s - min_val) / (max_val - min_val)
                else:
                    normalized_scores[method] = s
        
        # Score ensemble
        ensemble_score = pd.Series(0.0, index=self.feature_cols)
        for method, weight in weights.items():
            if method in normalized_scores:
                ensemble_score += normalized_scores[method] * weight
        
        ensemble_score = ensemble_score.sort_values(ascending=False)
        selected = ensemble_score.head(self.n_features).index.tolist()
        
        self.selected_features = selected
        self.feature_scores['ensemble'] = ensemble_score.to_dict()
        
        logger.info(f"\nTop 10 features ENSEMBLE:")
        for feat, score in ensemble_score.head(10).items():
            logger.info(f"  {feat}: {score:.4f}")
        
        return selected, ensemble_score
    
    def evaluate_selection(self, feature_subset):
        """
        Évalue la performance avec un sous-ensemble de features.
        
        Returns:
            Dict avec accuracy et autres métriques
        """
        X_train_subset = self.X_train[feature_subset]
        X_test_subset = self.X_test[feature_subset]
        
        # Entraîner XGBoost
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train_subset, self.y_train)
        
        # Évaluer
        y_pred = model.predict(X_test_subset)
        accuracy = accuracy_score(self.y_test, y_pred)
        
        return {
            'n_features': len(feature_subset),
            'accuracy': accuracy,
            'features': feature_subset
        }
    
    def compare_methods(self):
        """Compare toutes les méthodes de sélection."""
        logger.info("\n" + "="*70)
        logger.info("COMPARAISON DES MÉTHODES DE SÉLECTION")
        logger.info("="*70)
        
        results = []
        
        # Baseline: toutes les features
        logger.info("\n[1/5] Baseline (toutes les features)")
        baseline = self.evaluate_selection(self.feature_cols)
        baseline['method'] = 'all_features'
        results.append(baseline)
        logger.info(f"  Accuracy: {baseline['accuracy']:.4f} ({len(self.feature_cols)} features)")
        
        # ANOVA F
        logger.info(f"\n[2/5] ANOVA F ({self.n_features} features)")
        features_anova = self.select_anova_f()[0]
        result_anova = self.evaluate_selection(features_anova)
        result_anova['method'] = 'anova_f'
        results.append(result_anova)
        logger.info(f"  Accuracy: {result_anova['accuracy']:.4f}")
        
        # Mutual Info
        logger.info(f"\n[3/5] Mutual Information ({self.n_features} features)")
        features_mi = self.select_mutual_info()[0]
        result_mi = self.evaluate_selection(features_mi)
        result_mi['method'] = 'mutual_info'
        results.append(result_mi)
        logger.info(f"  Accuracy: {result_mi['accuracy']:.4f}")
        
        # XGB Importance
        logger.info(f"\n[4/5] XGB Importance ({self.n_features} features)")
        features_xgb = self.select_xgb_importance()[0]
        result_xgb = self.evaluate_selection(features_xgb)
        result_xgb['method'] = 'xgb_importance'
        results.append(result_xgb)
        logger.info(f"  Accuracy: {result_xgb['accuracy']:.4f}")
        
        # Ensemble
        logger.info(f"\n[5/5] Ensemble ({self.n_features} features)")
        features_ensemble = self.ensemble_selection()[0]
        result_ensemble = self.evaluate_selection(features_ensemble)
        result_ensemble['method'] = 'ensemble'
        results.append(result_ensemble)
        logger.info(f"  Accuracy: {result_ensemble['accuracy']:.4f}")
        
        # Résumé
        logger.info("\n" + "="*70)
        logger.info("RÉSULTATS COMPARATIFS")
        logger.info("="*70)
        for r in results:
            logger.info(f"{r['method']:20s}: {r['accuracy']:.4f} ({r['n_features']} features)")
        
        # Trouver la meilleure
        best = max(results, key=lambda x: x['accuracy'])
        logger.info(f"\n🏆 Meilleure méthode: {best['method']}")
        logger.info(f"   Accuracy: {best['accuracy']:.4f}")
        
        self.comparison_results = results
        self.best_selection = best
        
        return results
    
    def save_selection(self, output_path, method='ensemble'):
        """Sauvegarde la sélection de features."""
        if method == 'ensemble':
            features = self.selected_features
        elif method == 'best':
            features = self.best_selection['features']
        else:
            features = self.selected_features
        
        output = {
            'n_features': len(features),
            'features': features,
            'selection_method': method,
            'all_scores': self.feature_scores
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"✅ Sélection sauvegardée: {output_path}")
        return output_path


def run_feature_selection(features_path, output_dir, n_features=35):
    """
    Pipeline complet de feature selection.
    
    Args:
        features_path: Chemin vers features_v3.parquet
        output_dir: Dossier de sortie
        n_features: Nombre de features à sélectionner
    """
    logger.info("="*70)
    logger.info("FEATURE SELECTION - NBA-22 OPTIMIZATION")
    logger.info("="*70)
    
    selector = FeatureSelector(n_features=n_features)
    
    # Charger données
    selector.load_data(features_path)
    selector.split_temporal()
    
    # Comparer méthodes
    results = selector.compare_methods()
    
    # Sauvegarder
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    selector.save_selection(output_dir / 'selected_features.json', method='best')
    
    # Sauvegarder aussi la comparaison
    with open(output_dir / 'selection_comparison.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("\n✅ Feature selection terminée!")
    
    return selector


if __name__ == '__main__':
    # Exécution
    selector = run_feature_selection(
        features_path="data/gold/ml_features/features_v3.parquet",
        output_dir="results/feature_selection",
        n_features=35
    )
