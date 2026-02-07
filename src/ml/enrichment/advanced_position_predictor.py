"""
Prédicteur de position avancé - Phase 3.

Utilise Random Forest avec:
- Plus de features (BMI, ratios, etc.)
- Équilibrage des classes
- Validation croisée
- Meilleure accuracy visée: 80%+
"""

import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class AdvancedPositionPredictor:
    """
    Prédicteur de position avancé avec Random Forest.
    
    Features:
    - height_cm, weight_kg
    - bmi (Body Mass Index)
    - height_weight_ratio
    - weight_per_cm
    - bmi_category (underweight, normal, overweight, obese)
    
    Usage:
        predictor = AdvancedPositionPredictor()
        predictor.train(known_players)
        prediction = predictor.predict(height=200, weight=98)
        # {'position': 'F', 'confidence': 0.89, 'probabilities': {...}}
    """
    
    # Mapping positions simplifiées (5 classes principales)
    POSITION_MAPPING = {
        'G': 'G',
        'F': 'F', 
        'C': 'C',
        'G-F': 'G-F',
        'F-G': 'G-F',
        'F-C': 'F-C',
        'C-F': 'F-C',
        'C-G': 'G',  # Rare, map vers G
        'G-C': 'G'   # Rare, map vers G
    }
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialise le prédicteur avancé."""
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.training_stats = {}
        self.classes_ = None
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def _extract_features(self, player: Dict) -> Optional[np.ndarray]:
        """
        Extrait les features avancées d'un joueur.
        
        Features:
        1. height_cm
        2. weight_kg
        3. bmi
        4. height_weight_ratio (height/weight)
        5. weight_per_cm (weight/height)
        6. bmi_category_encoded
        7. height_squared (pour non-linéarité)
        8. weight_squared
        """
        height = player.get('height_cm')
        weight = player.get('weight_kg')
        
        if not height or not weight or height <= 0 or weight <= 0:
            return None
        
        # Calculs de base
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        # Ratios
        height_weight_ratio = height / weight
        weight_per_cm = weight / height
        
        # BMI category (0-3)
        if bmi < 18.5:
            bmi_category = 0  # Underweight
        elif bmi < 25:
            bmi_category = 1  # Normal
        elif bmi < 30:
            bmi_category = 2  # Overweight
        else:
            bmi_category = 3  # Obese
        
        # Features au carré (pour capturer non-linéarité)
        height_squared = height ** 2
        weight_squared = weight ** 2
        
        return np.array([
            height,
            weight,
            bmi,
            height_weight_ratio,
            weight_per_cm,
            bmi_category,
            height_squared,
            weight_squared
        ])
    
    def _prepare_data(self, players: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prépare les données d'entraînement."""
        X = []
        y = []
        
        for player in players:
            features = self._extract_features(player)
            position = player.get('position')
            
            if features is not None and position:
                # Mapper vers classes principales
                mapped_position = self.POSITION_MAPPING.get(position, position)
                X.append(features)
                y.append(mapped_position)
        
        return np.array(X), np.array(y)
    
    def train(self, players: List[Dict], 
              use_smote: bool = True,
              test_size: float = 0.2) -> bool:
        """
        Entraîne le modèle Random Forest.
        
        Args:
            players: Joueurs avec position connue
            use_smote: Si True, équilibre les classes avec SMOTE
            test_size: Proportion pour le jeu de test
            
        Returns:
            True si entraînement réussi
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import classification_report, accuracy_score
        except ImportError:
            logger.error("scikit-learn non installé")
            return False
        
        # Préparer données
        X, y = self._prepare_data(players)
        
        if len(X) < 50:
            logger.warning(f"Pas assez de données: {len(X)} échantillons")
            return False
        
        logger.info(f"Préparation: {len(X)} échantillons, {len(set(y))} classes")
        
        # Distribution initiale
        class_dist = Counter(y)
        logger.info(f"Distribution: {dict(class_dist)}")
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # SMOTE pour équilibrer (optionnel)
        if use_smote:
            try:
                from imblearn.over_sampling import SMOTE
                smote = SMOTE(random_state=42)
                X_train, y_train = smote.fit_resample(X_train, y_train)
                logger.info(f"Après SMOTE: {len(X_train)} échantillons")
            except ImportError:
                logger.warning("imbalanced-learn non installé, SMOTE ignoré")
        
        # Normalisation
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Entraîner Random Forest
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train_scaled, y_train)
        self.classes_ = self.model.classes_
        
        # Évaluer
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"✅ Modèle entraîné - Accuracy: {accuracy:.1%}")
        
        # Détails par classe
        report = classification_report(y_test, y_pred, output_dict=True)
        
        self.training_stats = {
            'n_samples': len(X),
            'n_features': X.shape[1],
            'n_classes': len(self.classes_),
            'accuracy': accuracy,
            'classes': list(self.classes_),
            'feature_importance': dict(zip(
                ['height', 'weight', 'bmi', 'h_w_ratio', 'w_per_cm', 
                 'bmi_cat', 'h_sq', 'w_sq'],
                self.model.feature_importances_.tolist()
            ))
        }
        
        self.is_trained = True
        return True
    
    def predict(self, height: float, weight: float,
                return_proba: bool = True) -> Optional[Dict]:
        """
        Prédit la position avec confiance.
        
        Args:
            height: Taille en cm
            weight: Poids en kg
            return_proba: Si True, retourne les probabilités
            
        Returns:
            Dict avec 'position', 'confidence', 'probabilities', 'all_positions'
        """
        if not self.is_trained or self.model is None:
            logger.warning("Modèle non entraîné")
            return None
        
        # Créer features
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        features = np.array([[
            height,
            weight,
            bmi,
            height / weight,
            weight / height,
            1 if 18.5 <= bmi < 25 else (2 if bmi < 30 else 3),
            height ** 2,
            weight ** 2
        ]])
        
        # Normaliser
        features_scaled = self.scaler.transform(features)
        
        # Prédire
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Construire résultat
        result = {
            'position': prediction,
            'confidence': float(np.max(probabilities)),
            'all_positions': {
                cls: float(prob) 
                for cls, prob in zip(self.classes_, probabilities)
            }
        }
        
        # Alternative (2ème meilleure prédiction)
        sorted_indices = np.argsort(probabilities)[::-1]
        if len(sorted_indices) > 1:
            result['alternative'] = self.classes_[sorted_indices[1]]
            result['alternative_confidence'] = float(probabilities[sorted_indices[1]])
        
        return result
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Retourne l'importance des features."""
        if not self.is_trained:
            return {}
        
        return self.training_stats.get('feature_importance', {})
    
    def save_model(self, path: str):
        """Sauvegarde le modèle."""
        if not self.is_trained:
            logger.warning("Modèle non entraîné")
            return
        
        data = {
            'model': self.model,
            'scaler': self.scaler,
            'classes': self.classes_,
            'training_stats': self.training_stats
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Modèle sauvegardé: {path}")
    
    def load_model(self, path: str):
        """Charge un modèle."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.scaler = data['scaler']
        self.classes_ = data['classes']
        self.training_stats = data['training_stats']
        self.is_trained = True
        
        logger.info(f"Modèle chargé: {path}")
        logger.info(f"  Accuracy: {self.training_stats.get('accuracy', 0):.1%}")


def compare_models(players: List[Dict]):
    """Compare K-Means vs Random Forest."""
    print("\n" + "="*70)
    print("COMPARAISON MODÈLES")
    print("="*70)
    
    # K-Means (baseline)
    from position_predictor import PositionPredictor
    
    print("\n1. K-Means (Phase 2):")
    km = PositionPredictor()
    km.train(players)
    print(f"   Accuracy: {km.training_stats.get('accuracy_estimate', 0):.1f}%")
    
    # Random Forest
    print("\n2. Random Forest (Phase 3):")
    rf = AdvancedPositionPredictor()
    rf.train(players, use_smote=False)
    print(f"   Accuracy: {rf.training_stats.get('accuracy', 0):.1f}%")
    
    # Feature importance
    print("\n3. Importance des features (RF):")
    importance = rf.get_feature_importance()
    for feature, imp in sorted(importance.items(), key=lambda x: -x[1]):
        print(f"   {feature:15}: {imp:.1%}")
    
    # Test prédiction
    print("\n4. Test prédiction (200cm, 98kg):")
    
    km_result = km.predict(200, 98)
    print(f"   K-Means:  {km_result['position']} ({km_result['confidence']:.1%})")
    
    rf_result = rf.predict(200, 98)
    print(f"   RF:       {rf_result['position']} ({rf_result['confidence']:.1%})")
    print(f"   Probas:   {rf_result['all_positions']}")


if __name__ == "__main__":
    # Test
    print("Test AdvancedPositionPredictor")
    
    test_players = [
        {'height_cm': 191, 'weight_kg': 87, 'position': 'G'},
        {'height_cm': 195, 'weight_kg': 90, 'position': 'G'},
        {'height_cm': 201, 'weight_kg': 100, 'position': 'F'},
        {'height_cm': 205, 'weight_kg': 105, 'position': 'F'},
        {'height_cm': 211, 'weight_kg': 115, 'position': 'C'},
        {'height_cm': 216, 'weight_kg': 120, 'position': 'C'},
    ]
    
    predictor = AdvancedPositionPredictor()
    
    if predictor.train(test_players, use_smote=False):
        result = predictor.predict(200, 98)
        print(f"\nPrédiction: {result}")
