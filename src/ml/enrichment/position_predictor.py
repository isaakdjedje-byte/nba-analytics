"""
Prédicteur de position basé sur K-Means clustering.

Entraîné sur les joueurs avec position connue pour prédire
la position des joueurs sans métadonnées.
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class PositionPredictor:
    """
    Prédicteur de position basketball par clustering.
    
    Utilise K-Means sur les features physiques (taille, poids, BMI)
    pour prédire la position (G, F, C, G-F, F-C, etc.).
    
    Usage:
        predictor = PositionPredictor()
        predictor.train(known_players)
        prediction = predictor.predict(height=200, weight=100)
        # {'position': 'F', 'confidence': 0.85, 'alternative': 'F-C'}
    """
    
    # Mapping positions simplifiées vers catégories principales
    POSITION_CATEGORIES = {
        'G': 'Guard',
        'F': 'Forward', 
        'C': 'Center',
        'G-F': 'Guard-Forward',
        'F-G': 'Forward-Guard',
        'F-C': 'Forward-Center',
        'C-F': 'Center-Forward',
        'C-G': 'Center-Guard',
        'G-C': 'Guard-Center'
    }
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialise le prédicteur.
        
        Args:
            model_path: Chemin vers un modèle sauvegardé (optional)
        """
        self.model = None
        self.is_trained = False
        self.training_stats = {}
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def _extract_features(self, player: Dict) -> Optional[np.ndarray]:
        """
        Extrait les features physiques d'un joueur.
        
        Features: [height_cm, weight_kg, bmi]
        
        Returns:
            Array numpy de features ou None si données invalides
        """
        height = player.get('height_cm')
        weight = player.get('weight_kg')
        
        if not height or not weight or height <= 0 or weight <= 0:
            return None
        
        # Calcul BMI
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        return np.array([height, weight, bmi])
    
    def train(self, players: List[Dict], min_samples_per_class: int = 10) -> bool:
        """
        Entraîne le modèle sur les joueurs avec position connue.
        
        Args:
            players: Liste de joueurs avec 'position', 'height_cm', 'weight_kg'
            min_samples_per_class: Minimum d'échantillons par classe
            
        Returns:
            True si entraînement réussi
        """
        try:
            from sklearn.cluster import KMeans
            from collections import Counter
        except ImportError:
            logger.error("scikit-learn non installé. Installez: pip install scikit-learn")
            return False
        
        # Filtrer joueurs avec position et données physiques
        valid_players = []
        for p in players:
            pos = p.get('position')
            features = self._extract_features(p)
            if pos and features is not None:
                valid_players.append((p, features, pos))
        
        if len(valid_players) < 50:
            logger.warning(f"Pas assez de données d'entraînement: {len(valid_players)} joueurs")
            return False
        
        logger.info(f"Entraînement sur {len(valid_players)} joueurs avec position connue")
        
        # Analyse des positions
        position_counts = Counter(pos for _, _, pos in valid_players)
        logger.info(f"Distribution positions: {dict(position_counts)}")
        
        # Regrouper par catégories principales
        X = np.array([features for _, features, _ in valid_players])
        y = [pos for _, _, pos in valid_players]
        
        # Entraîner K-Means avec 5 clusters (G, F, C, G-F, F-C)
        n_clusters = min(5, len(position_counts))
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.model.fit(X)
        
        # Associer clusters aux positions
        self._assign_clusters_to_positions(X, y)
        
        # Statistiques
        self.training_stats = {
            'n_samples': len(valid_players),
            'n_clusters': n_clusters,
            'positions': list(position_counts.keys()),
            'accuracy_estimate': self._estimate_accuracy(X, y)
        }
        
        self.is_trained = True
        logger.info(f"✅ Modèle entraîné - Accuracy estimée: {self.training_stats['accuracy_estimate']:.1f}%")
        
        return True
    
    def _assign_clusters_to_positions(self, X: np.ndarray, y: List[str]):
        """Associe chaque cluster à la position majoritaire."""
        from collections import Counter
        
        cluster_labels = self.model.labels_
        self.cluster_to_position = {}
        self.cluster_confidence = {}
        
        for cluster_id in range(self.model.n_clusters):
            # Joueurs dans ce cluster
            mask = cluster_labels == cluster_id
            positions_in_cluster = [pos for i, pos in enumerate(y) if mask[i]]
            
            if positions_in_cluster:
                # Position majoritaire
                counter = Counter(positions_in_cluster)
                most_common = counter.most_common(1)[0]
                position, count = most_common
                total = len(positions_in_cluster)
                confidence = count / total
                
                self.cluster_to_position[cluster_id] = position
                self.cluster_confidence[cluster_id] = confidence
                
                logger.debug(f"Cluster {cluster_id}: {position} ({confidence:.1%} confiance)")
    
    def _estimate_accuracy(self, X: np.ndarray, y: List[str]) -> float:
        """Estime l'accuracy par validation sur données d'entraînement."""
        predictions = self.model.predict(X)
        correct = 0
        
        for i, pred_cluster in enumerate(predictions):
            pred_pos = self.cluster_to_position.get(pred_cluster, 'Unknown')
            if pred_pos == y[i]:
                correct += 1
        
        return (correct / len(y)) * 100
    
    def predict(self, height: float, weight: float, 
                confidence_threshold: float = 0.6) -> Optional[Dict]:
        """
        Prédit la position d'un joueur.
        
        Args:
            height: Taille en cm
            weight: Poids en kg
            confidence_threshold: Seuil de confiance minimum
            
        Returns:
            Dict avec 'position', 'confidence', 'alternative' ou None
        """
        if not self.is_trained or self.model is None:
            logger.warning("Modèle non entraîné")
            return None
        
        # Calculer features
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        features = np.array([[height, weight, bmi]])
        
        # Prédire cluster
        cluster = self.model.predict(features)[0]
        
        # Récupérer position et confiance
        position = self.cluster_to_position.get(cluster)
        confidence = self.cluster_confidence.get(cluster, 0.0)
        
        if position is None:
            return None
        
        # Alternative (2ème meilleure position)
        distances = self.model.transform(features)[0]
        sorted_clusters = np.argsort(distances)
        
        alternative = None
        if len(sorted_clusters) > 1:
            alt_cluster = sorted_clusters[1]
            alternative = self.cluster_to_position.get(alt_cluster)
        
        # Vérifier seuil de confiance
        if confidence < confidence_threshold:
            logger.debug(f"Confiance trop faible: {confidence:.1%} < {confidence_threshold:.1%}")
            return None
        
        return {
            'position': position,
            'confidence': round(confidence, 3),
            'alternative': alternative,
            'cluster_id': int(cluster)
        }
    
    def save_model(self, path: str):
        """Sauvegarde le modèle entraîné."""
        if not self.is_trained:
            logger.warning("Modèle non entraîné, impossible de sauvegarder")
            return
        
        data = {
            'model': self.model,
            'cluster_to_position': self.cluster_to_position,
            'cluster_confidence': self.cluster_confidence,
            'training_stats': self.training_stats
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Modèle sauvegardé: {path}")
    
    def load_model(self, path: str):
        """Charge un modèle sauvegardé."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.cluster_to_position = data['cluster_to_position']
        self.cluster_confidence = data['cluster_confidence']
        self.training_stats = data['training_stats']
        self.is_trained = True
        
        logger.info(f"Modèle chargé: {path}")
        logger.info(f"  Accuracy: {self.training_stats.get('accuracy_estimate', 0):.1f}%")


class CareerStatusInferencer:
    """
    Infère le statut de carrière (is_active) à partir des années.
    """
    
    @staticmethod
    def infer(from_year: Optional[int], to_year: Optional[int], 
              current_year: int = 2026) -> Optional[bool]:
        """
        Infère si un joueur est actif.
        
        Args:
            from_year: Année de début
            to_year: Année de fin
            current_year: Année courante
            
        Returns:
            True si actif, False sinon, None si inconnu
        """
        if to_year is not None:
            # Si to_year >= current_year, le joueur est actif
            return to_year >= current_year
        
        if from_year is not None:
            # Si from_year est récent (5 dernières années), probablement actif
            return (current_year - from_year) < 5
        
        return None


def train_and_save_position_model(players: List[Dict], 
                                  output_path: str = "models/position_predictor.pkl") -> bool:
    """
    Fonction utilitaire pour entraîner et sauvegarder le modèle.
    
    Args:
        players: Joueurs avec position connue
        output_path: Chemin de sauvegarde
        
    Returns:
        True si succès
    """
    predictor = PositionPredictor()
    
    if predictor.train(players):
        predictor.save_model(output_path)
        return True
    
    return False


if __name__ == "__main__":
    # Test rapide
    print("Test PositionPredictor:")
    
    # Données de test
    test_players = [
        {'height_cm': 191, 'weight_kg': 87, 'position': 'G'},
        {'height_cm': 198, 'weight_kg': 95, 'position': 'G'},
        {'height_cm': 201, 'weight_kg': 100, 'position': 'F'},
        {'height_cm': 203, 'weight_kg': 104, 'position': 'F'},
        {'height_cm': 211, 'weight_kg': 115, 'position': 'C'},
        {'height_cm': 216, 'weight_kg': 120, 'position': 'C'},
    ]
    
    predictor = PositionPredictor()
    
    if predictor.train(test_players):
        # Test prédiction
        result = predictor.predict(height=200, weight=98)
        print(f"\nPrédiction pour 200cm/98kg:")
        print(f"  Position: {result['position']}")
        print(f"  Confiance: {result['confidence']:.1%}")
        print(f"  Alternative: {result['alternative']}")
