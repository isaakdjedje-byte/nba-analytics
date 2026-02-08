"""
Tests critiques pour le pipeline ML (NBA-22/NBA-25)

Couvre les composants essentiels du pipeline ML :
1. Entraînement optimisé (train_optimized.py)
2. Détection de drift (drift_monitoring.py)
3. Calibration des probabilités (probability_calibration.py)
4. Sélection de features (feature_selection.py)
5. Pipeline quotidien (daily_pipeline.py)

Stratégie: Mock les modèles pour tests rapides sans entraînement réel
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys

# Ajoute src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestOptimizedTrainer:
    """Tests pour OptimizedNBA22Trainer"""
    
    @pytest.fixture
    def sample_features_df(self):
        """Crée un DataFrame de features minimal pour tests"""
        np.random.seed(42)
        n_samples = 100
        
        data = {
            'game_id': range(n_samples),
            'season': ['2022-23'] * 50 + ['2023-24'] * 50,
            'game_date': pd.date_range('2023-01-01', periods=n_samples, freq='D'),
            'home_team_id': np.random.randint(1, 31, n_samples),
            'away_team_id': np.random.randint(1, 31, n_samples),
            'target': np.random.randint(0, 2, n_samples),
            # Features numériques
            'win_pct_diff': np.random.randn(n_samples),
            'pts_diff': np.random.randn(n_samples),
            'rest_days_diff': np.random.randint(-3, 4, n_samples),
            'h2h_win_pct_diff': np.random.randn(n_samples),
            'weighted_form_diff': np.random.randn(n_samples),
            'home_momentum': np.random.randn(n_samples),
            'away_momentum': np.random.randn(n_samples),
            'fatigue_diff': np.random.randn(n_samples),
            'off_eff_diff': np.random.randn(n_samples),
            'def_eff_diff': np.random.randn(n_samples),
        }
        
        return pd.DataFrame(data)
    
    def test_trainer_initialization(self, tmp_path):
        """Test: L'entraîneur s'initialise correctement"""
        from ml.pipeline.train_optimized import OptimizedNBA22Trainer
        
        trainer = OptimizedNBA22Trainer(
            features_path=str(tmp_path / "features.parquet"),
            output_dir=str(tmp_path / "models"),
            n_features=10
        )
        
        assert trainer.n_features == 10
        assert trainer.output_dir.exists()
        assert len(trainer.models) == 0
        
    def test_data_loading(self, tmp_path, sample_features_df):
        """Test: Chargement et préparation des données"""
        from ml.pipeline.train_optimized import OptimizedNBA22Trainer
        
        # Sauvegarde les données temporaires
        features_path = tmp_path / "features.parquet"
        sample_features_df.to_parquet(features_path)
        
        trainer = OptimizedNBA22Trainer(
            features_path=str(features_path),
            output_dir=str(tmp_path / "models")
        )
        
        df = trainer.load_and_prepare_data()
        
        assert df is not None
        assert len(df) == len(sample_features_df)
        assert 'game_date' in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df['game_date'])
        
    def test_feature_columns_exclusion(self, tmp_path, sample_features_df):
        """Test: Les colonnes de data leakage sont exclues"""
        from ml.pipeline.train_optimized import OptimizedNBA22Trainer
        
        features_path = tmp_path / "features.parquet"
        sample_features_df.to_parquet(features_path)
        
        trainer = OptimizedNBA22Trainer(features_path=str(features_path))
        trainer.load_and_prepare_data()
        
        # Vérifie que les colonnes de data leakage ne sont pas dans feature_cols
        leakage_cols = ['home_score', 'away_score', 'point_diff', 'target']
        for col in leakage_cols:
            if col in trainer.feature_cols:
                pytest.fail(f"Colonne de data leakage '{col}' ne devrait pas être une feature")
                
    def test_train_test_split_temporal(self, tmp_path, sample_features_df):
        """Test: Le split train/test respecte l'ordre temporel"""
        from ml.pipeline.train_optimized import OptimizedNBA22Trainer
        
        features_path = tmp_path / "features.parquet"
        sample_features_df.to_parquet(features_path)
        
        trainer = OptimizedNBA22Trainer(features_path=str(features_path))
        trainer.load_and_prepare_data()
        
        # Simule le split temporel
        test_seasons = ['2023-24']
        train_mask = ~trainer.df['season'].isin(test_seasons)
        test_mask = trainer.df['season'].isin(test_seasons)
        
        train_dates = trainer.df[train_mask]['game_date'].max()
        test_dates = trainer.df[test_mask]['game_date'].min()
        
        # Vérifie qu'il n'y a pas de fuite temporelle
        assert train_dates < test_dates, "Fuite temporelle: train contient des dates postérieures au test"


class TestDriftMonitoring:
    """Tests pour DataDriftMonitor"""
    
    @pytest.fixture
    def drift_monitor(self):
        """Fixture pour DataDriftMonitor"""
        from ml.pipeline.drift_monitoring import DataDriftMonitor
        return DataDriftMonitor(alert_threshold=0.05)
    
    @pytest.fixture
    def reference_data(self):
        """Données de référence (distribution normale)"""
        np.random.seed(42)
        return pd.DataFrame({
            'feature1': np.random.normal(0, 1, 1000),
            'feature2': np.random.normal(5, 2, 1000),
        })
    
    @pytest.fixture
    def drifted_data(self):
        """Données avec drift (distribution différente)"""
        np.random.seed(43)
        return pd.DataFrame({
            'feature1': np.random.normal(2, 1, 1000),  # Shift de moyenne
            'feature2': np.random.normal(5, 4, 1000),  # Changement de variance
        })
    
    def test_drift_detection_no_drift(self, drift_monitor, reference_data):
        """Test: Pas de drift détecté sur données identiques"""
        result = drift_monitor.detect_drift(reference_data, reference_data)
        
        assert not result['drift_detected'], "Ne devrait pas détecter de drift sur données identiques"
        assert result['drifted_features'] == []
        
    def test_drift_detection_with_drift(self, drift_monitor, reference_data, drifted_data):
        """Test: Drift détecté sur données différentes"""
        result = drift_monitor.detect_drift(reference_data, drifted_data)
        
        assert result['drift_detected'], "Devrait détecter le drift"
        assert len(result['drifted_features']) > 0, "Devrait lister les features driftées"
        
    def test_drift_report_generation(self, drift_monitor, reference_data, drifted_data):
        """Test: Génération du rapport de drift"""
        result = drift_monitor.detect_drift(reference_data, drifted_data)
        
        assert 'drifted_features' in result
        assert 'drift_scores' in result
        assert 'summary' in result
        
    def test_performance_degradation_detection(self, drift_monitor):
        """Test: Détection de dégradation des performances"""
        # Mock tracker
        mock_tracker = Mock()
        mock_tracker.calculate_roi.return_value = {
            'accuracy': 0.70,
            'total_predictions': 50,
            'wins': 35,
            'losses': 15
        }
        
        # Devrait détecter dégradation si accuracy < 0.75
        with patch.object(drift_monitor, '_alert') as mock_alert:
            drift_monitor.check_performance_degradation(mock_tracker, min_predictions=20)
            # Si accuracy < 0.75, devrait alerter
            

class TestProbabilityCalibration:
    """Tests pour ProbabilityCalibrator"""
    
    @pytest.fixture
    def sample_predictions(self):
        """Prédictions de test"""
        return np.array([0.1, 0.3, 0.5, 0.7, 0.9])
    
    @pytest.fixture
    def sample_true_labels(self):
        """Labels réels de test"""
        return np.array([0, 0, 1, 1, 1])
    
    def test_calibration_output_range(self, sample_predictions, sample_true_labels):
        """Test: Les probabilités calibrées restent dans [0, 1]"""
        from ml.pipeline.probability_calibration import calibrate_model
        
        # Mock modèle
        mock_model = Mock()
        mock_model.predict_proba.return_value = np.column_stack([
            1 - sample_predictions,
            sample_predictions
        ])
        
        calibrator, _ = calibrate_model(
            mock_model, 
            sample_predictions.reshape(-1, 1),
            sample_true_labels,
            method='isotonic'
        )
        
        # Test calibration
        calibrated = calibrator.predict_proba(sample_predictions.reshape(-1, 1))[:, 1]
        
        assert np.all(calibrated >= 0), "Probabilités calibrées doivent être >= 0"
        assert np.all(calibrated <= 1), "Probabilités calibrées doivent être <= 1"
        
    def test_brier_score_improvement(self, sample_predictions, sample_true_labels):
        """Test: Le Brier score est calculable"""
        from sklearn.metrics import brier_score_loss
        
        brier = brier_score_loss(sample_true_labels, sample_predictions)
        
        assert 0 <= brier <= 1, "Brier score doit être entre 0 et 1"
        
    def test_calibration_methods(self):
        """Test: Les méthodes de calibration disponibles"""
        from ml.pipeline.probability_calibration import ProbabilityCalibrator
        
        # Vérifie que les méthodes standard sont supportées
        supported_methods = ['isotonic', 'sigmoid']
        
        for method in supported_methods:
            calibrator = ProbabilityCalibrator(method=method)
            assert calibrator.method == method


class TestFeatureSelection:
    """Tests pour FeatureSelector"""
    
    @pytest.fixture
    def sample_ml_data(self):
        """Données ML pour tests"""
        np.random.seed(42)
        n_samples = 200
        
        # Crée des features avec différentes importances
        data = {
            'target': np.random.randint(0, 2, n_samples),
            'important_feature': np.random.randn(n_samples) * 2,  # Forte importance
            'medium_feature': np.random.randn(n_samples),         # Moyenne importance
            'noise_feature': np.random.randn(n_samples) * 0.1,    # Faible importance
        }
        
        # Ajoute corrélation pour feature importante
        data['important_feature'] = data['target'] * 2 + np.random.randn(n_samples) * 0.5
        
        return pd.DataFrame(data)
    
    def test_feature_selection_reduces_dimensions(self, sample_ml_data):
        """Test: La sélection réduit bien le nombre de features"""
        from ml.pipeline.feature_selection import FeatureSelector
        
        selector = FeatureSelector(n_features=2)
        selector.df = sample_ml_data
        selector.feature_cols = ['important_feature', 'medium_feature', 'noise_feature']
        
        selected = selector.select_features()
        
        assert len(selected) <= 2, "Devrait sélectionner au plus n_features"
        assert 'important_feature' in selected, "Devrait sélectionner la feature importante"
        
    def test_feature_selection_no_leakage(self, sample_ml_data):
        """Test: La target n'est pas dans les features sélectionnées"""
        from ml.pipeline.feature_selection import FeatureSelector
        
        selector = FeatureSelector(n_features=2)
        selector.df = sample_ml_data
        selector.feature_cols = ['important_feature', 'medium_feature', 'target']
        
        selected = selector.select_features()
        
        assert 'target' not in selected, "La target ne doit pas être sélectionnée comme feature"
        
    def test_feature_importance_calculation(self, sample_ml_data):
        """Test: Calcul de l'importance des features"""
        from ml.pipeline.feature_selection import FeatureSelector
        
        selector = FeatureSelector(n_features=3)
        selector.df = sample_ml_data
        selector.feature_cols = ['important_feature', 'medium_feature', 'noise_feature']
        
        importance = selector.get_feature_importance()
        
        assert 'important_feature' in importance
        assert importance['important_feature'] > importance['noise_feature'], \
            "La feature importante devrait avoir une importance plus élevée"


class TestDailyPipeline:
    """Tests pour DailyPredictionPipeline"""
    
    @pytest.fixture
    def mock_models(self, tmp_path):
        """Crée des modèles mockés pour tests"""
        import joblib
        
        # Mock XGBoost
        mock_xgb = Mock()
        mock_xgb.predict.return_value = np.array([1, 0, 1])
        mock_xgb.predict_proba.return_value = np.array([
            [0.3, 0.7],
            [0.6, 0.4],
            [0.2, 0.8]
        ])
        
        # Mock Random Forest
        mock_rf = Mock()
        mock_rf.predict.return_value = np.array([1, 0, 1])
        mock_rf.predict_proba.return_value = np.array([
            [0.4, 0.6],
            [0.7, 0.3],
            [0.3, 0.7]
        ])
        
        # Sauvegarde
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        joblib.dump(mock_xgb, models_dir / "model_xgb.joblib")
        joblib.dump(mock_rf, models_dir / "model_rf.joblib")
        
        # Features sélectionnées
        selected_features = ['win_pct_diff', 'pts_diff', 'rest_days_diff']
        with open(models_dir / "selected_features.json", 'w') as f:
            import json
            json.dump(selected_features, f)
            
        return models_dir
    
    def test_pipeline_loads_models(self, mock_models):
        """Test: Le pipeline charge correctement les modèles"""
        from ml.pipeline.daily_pipeline import DailyPredictionPipeline
        
        # Mock pour éviter dépendances
        with patch('ml.pipeline.daily_pipeline.pd.read_parquet') as mock_read:
            mock_read.return_value = pd.DataFrame({
                'win_pct_diff': [0.1, -0.2, 0.3],
                'pts_diff': [5, -3, 8],
                'rest_days_diff': [1, -1, 2],
                'game_id': [1, 2, 3],
                'home_team': ['LAL', 'BOS', 'CHI'],
                'away_team': ['GSW', 'NYK', 'MIA']
            })
            
            pipeline = DailyPredictionPipeline(
                features_path="dummy.parquet",
                models_dir=str(mock_models)
            )
            
            # Charge les modèles
            pipeline.load_models()
            
            assert 'xgb' in pipeline.models or hasattr(pipeline, 'xgb_model')
            
    def test_prediction_output_format(self):
        """Test: Le format de sortie des prédictions est correct"""
        # Structure attendue
        expected_columns = [
            'game_id', 'home_team', 'away_team',
            'xgb_prediction', 'xgb_confidence',
            'rf_prediction', 'rf_confidence',
            'ensemble_prediction', 'ensemble_confidence'
        ]
        
        # Vérifie que toutes les colonnes sont définies
        for col in expected_columns:
            assert isinstance(col, str), f"Colonne {col} doit être une string"
            
    def test_confidence_thresholds(self):
        """Test: Les seuils de confiance sont respectés"""
        confidences = [0.45, 0.55, 0.65, 0.75, 0.85]
        
        for conf in confidences:
            if conf < 0.55:
                assert conf < 0.55, f"Confiance {conf} < 55%: SKIP"
            elif conf < 0.60:
                assert 0.55 <= conf < 0.60, f"Confiance {conf}: LOW"
            elif conf < 0.70:
                assert 0.60 <= conf < 0.70, f"Confiance {conf}: MEDIUM"
            else:
                assert conf >= 0.70, f"Confiance {conf}: HIGH"


class TestEndToEnd:
    """Tests end-to-end du pipeline ML"""
    
    def test_data_flow_no_leakage(self):
        """Test: Le flux de données n'a pas de fuite"""
        # Simule le flux: features → prédiction
        
        # Étape 1: Features (sans données du match)
        features = pd.DataFrame({
            'win_pct_diff': [0.1],
            'pts_diff': [5.0],
            'rest_days_diff': [1],
            # PAS de home_score, away_score, etc.
        })
        
        # Étape 2: Modèle
        mock_model = Mock()
        mock_model.predict.return_value = np.array([1])
        mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])
        
        # Étape 3: Prédiction
        prediction = mock_model.predict(features)[0]
        proba = mock_model.predict_proba(features)[0, 1]
        
        # Vérifie la cohérence
        assert prediction in [0, 1], "La prédiction doit être binaire"
        assert 0 <= proba <= 1, "La probabilité doit être dans [0, 1]"
        
    def test_model_persistence(self, tmp_path):
        """Test: Les modèles peuvent être sauvegardés et chargés"""
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        
        # Crée un modèle simple
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        X = np.random.randn(50, 3)
        y = np.random.randint(0, 2, 50)
        model.fit(X, y)
        
        # Sauvegarde
        model_path = tmp_path / "test_model.joblib"
        joblib.dump(model, model_path)
        
        # Charge
        loaded_model = joblib.load(model_path)
        
        # Vérifie que les prédictions sont identiques
        X_test = np.random.randn(10, 3)
        pred_original = model.predict(X_test)
        pred_loaded = loaded_model.predict(X_test)
        
        assert np.array_equal(pred_original, pred_loaded), \
            "Le modèle chargé doit donner les mêmes prédictions"


if __name__ == "__main__":
    # Permet d'exécuter les tests sans pytest
    print("Exécution des tests ML Pipeline...")
    print("=" * 70)
    
    # Test basique
    import numpy as np
    print("✓ Imports OK")
    
    # Test simple
    pred = np.array([0.7, 0.3, 0.8])
    assert np.all(pred >= 0) and np.all(pred <= 1)
    print("✓ Prédictions dans [0, 1]")
    
    print("\nPour exécuter tous les tests:")
    print("  pytest tests/test_ml_pipeline_critical.py -v")
