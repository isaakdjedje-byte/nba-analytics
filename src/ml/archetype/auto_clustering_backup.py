#!/usr/bin/env python3
"""
NBA-23: Auto-Clustering avec sélection automatique du nombre optimal de clusters
Utilise K-Means, GMM, HDBSCAN et sélection par métriques multiples
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass

from sklearn.cluster import KMeans, SpectralClustering, AgglomerativeClustering, BisectingKMeans, MiniBatchKMeans
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif, VarianceThreshold
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from joblib import Parallel, delayed, Memory

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    print("WARNING: UMAP non disponible, utilisation de PCA")


@dataclass
class ClusteringResult:
    """Résultat d'un clustering"""
    algorithm: str
    n_clusters: int
    labels: np.ndarray
    probabilities: Optional[np.ndarray]
    silhouette: float
    calinski_harabasz: float
    davies_bouldin: float
    cluster_sizes: Dict[int, int]
    model: object
    reducer: Optional[object] = None


class AutoClustering:
    """
    Clustering automatique avec sélection du meilleur algorithme et k optimal
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.results = {}
        self.best_result = None
        
    def fit(self, X: np.ndarray, k_range: range = range(6, 13),
            min_cluster_size: int = 100, n_jobs: int = 1) -> ClusteringResult:
        """
        Exécute plusieurs algorithmes de clustering et sélectionne le meilleur
        
        Args:
            X: Données (features déjà normalisées ou non)
            k_range: Plage de k à tester
            min_cluster_size: Taille minimum d'un cluster valide
            n_jobs: Nombre de cores CPU (1 = séquentiel)
        """
        # Standardisation
        X_scaled = self.scaler.fit_transform(X)
        
        print(f"SEARCH: Clustering sur {X.shape[0]} échantillons, {X.shape[1]} features")
        print(f"   Test de k={k_range.start} à k={k_range.stop-1}")
        
        # Réduction dimensionnelle pour viz (2D)
        X_2d = self._reduce_dimension(X_scaled, n_components=2)
        
        # Test tous les algorithmes
        results = []
        
        # 1. K-Means
        print("\nTEST: Test K-Means...")
        for k in k_range:
            result = self._fit_kmeans(X_scaled, X_2d, k, min_cluster_size)
            if result:
                results.append(result)
                print(f"   k={k}: Silhouette={result.silhouette:.3f}, "
                      f"CH={result.calinski_harabasz:.0f}")
        
        # 2. Gaussian Mixture (GMM)
        print("\nTEST: Test GMM...")
        for k in k_range:
            result = self._fit_gmm(X_scaled, X_2d, k, min_cluster_size)
            if result:
                results.append(result)
                print(f"   k={k}: Silhouette={result.silhouette:.3f}")
        
        # 3. HDBSCAN (détection automatique k + outliers)
        if HDBSCAN_AVAILABLE:
            print("\nTEST: Test HDBSCAN...")
            result = self._fit_hdbscan(X_scaled, X_2d, min_cluster_size)
            if result:
                results.append(result)
                print(f"   Auto-k={result.n_clusters}: Silhouette={result.silhouette:.3f}")
        
        # Sélection du meilleur
        self.best_result = self._select_best(results)
        self.results = {r.algorithm: r for r in results}
        
        print(f"\nBEST: Meilleur modèle: {self.best_result.algorithm} "
              f"(k={self.best_result.n_clusters})")
        print(f"   Silhouette: {self.best_result.silhouette:.3f}")
        print(f"   Calinski-Harabasz: {self.best_result.calinski_harabasz:.0f}")
        print(f"   Davies-Bouldin: {self.best_result.davies_bouldin:.3f}")
        
        return self.best_result
    
    def _reduce_dimension(self, X: np.ndarray, n_components: int = 2) -> np.ndarray:
        """Réduction dimensionnelle avec UMAP ou PCA"""
        if UMAP_AVAILABLE and X.shape[0] > 100:
            reducer = umap.UMAP(n_components=n_components, random_state=self.random_state)
            return reducer.fit_transform(X)
        else:
            reducer = PCA(n_components=n_components)
            return reducer.fit_transform(X)
    
    def _fit_kmeans(self, X: np.ndarray, X_2d: np.ndarray, k: int,
                    min_cluster_size: int) -> Optional[ClusteringResult]:
        """Fit K-Means"""
        try:
            model = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = model.fit_predict(X)
            
            # Vérifie taille clusters
            unique, counts = np.unique(labels, return_counts=True)
            if any(c < min_cluster_size for c in counts):
                return None
            
            # Métriques
            sil = silhouette_score(X, labels)
            ch = calinski_harabasz_score(X, labels)
            db = davies_bouldin_score(X, labels)
            
            return ClusteringResult(
                algorithm=f"KMeans_k{k}",
                n_clusters=k,
                labels=labels,
                probabilities=None,
                silhouette=sil,
                calinski_harabasz=ch,
                davies_bouldin=db,
                cluster_sizes=dict(zip(unique, counts)),
                model=model
            )
        except Exception as e:
            print(f"   WARNING: K-Means k={k} échoué: {e}")
            return None
    
    def _fit_gmm(self, X: np.ndarray, X_2d: np.ndarray, k: int,
                 min_cluster_size: int) -> Optional[ClusteringResult]:
        """Fit Gaussian Mixture Model"""
        try:
            model = GaussianMixture(n_components=k, random_state=self.random_state,
                                   max_iter=200, n_init=5)
            labels = model.fit_predict(X)
            probs = model.predict_proba(X)
            
            # Vérifie taille clusters
            unique, counts = np.unique(labels, return_counts=True)
            if any(c < min_cluster_size for c in counts):
                return None
            
            # Métriques
            sil = silhouette_score(X, labels)
            ch = calinski_harabasz_score(X, labels)
            db = davies_bouldin_score(X, labels)
            
            return ClusteringResult(
                algorithm=f"GMM_k{k}",
                n_clusters=k,
                labels=labels,
                probabilities=probs,
                silhouette=sil,
                calinski_harabasz=ch,
                davies_bouldin=db,
                cluster_sizes=dict(zip(unique, counts)),
                model=model
            )
        except Exception as e:
            print(f"   WARNING: GMM k={k} échoué: {e}")
            return None
    
    def _fit_hdbscan(self, X: np.ndarray, X_2d: np.ndarray,
                     min_cluster_size: int) -> Optional[ClusteringResult]:
        """Fit HDBSCAN (détection automatique des clusters et outliers)"""
        if not HDBSCAN_AVAILABLE:
            return None
        
        try:
            # Ajuste min_cluster_size selon taille dataset
            min_cluster = max(min_cluster_size, len(X) // 20)
            
            model = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
                                   min_samples=5,
                                   metric='euclidean')
            labels = model.fit_predict(X)
            
            # Compte clusters valides (ignore -1 = outliers)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            
            if n_clusters < 4:  # Trop peu de clusters
                return None
            
            # Métriques (seulement sur points non-outliers)
            mask = labels != -1
            if mask.sum() < 100:
                return None
            
            sil = silhouette_score(X[mask], labels[mask])
            ch = calinski_harabasz_score(X[mask], labels[mask])
            db = davies_bouldin_score(X[mask], labels[mask])
            
            unique, counts = np.unique(labels[mask], return_counts=True)
            cluster_sizes = dict(zip(unique, counts))
            cluster_sizes[-1] = (labels == -1).sum()  # Ajoute outliers
            
            return ClusteringResult(
                algorithm=f"HDBSCAN_k{n_clusters}",
                n_clusters=n_clusters,
                labels=labels,
                probabilities=model.probabilities_,
                silhouette=sil,
                calinski_harabasz=ch,
                davies_bouldin=db,
                cluster_sizes=cluster_sizes,
                model=model
            )
        except Exception as e:
            print(f"   WARNING: HDBSCAN échoué: {e}")
            return None
    
    def _fit_minibatch_kmeans(self, X: np.ndarray, X_2d: np.ndarray, k: int,
                               min_cluster_size: int) -> Optional[ClusteringResult]:
        """Fit MiniBatch K-Means (plus rapide pour grands datasets)"""
        try:
            model = MiniBatchKMeans(n_clusters=k, random_state=self.random_state, 
                                   n_init=10, batch_size=1000)
            labels = model.fit_predict(X)
            
            # Vérifie taille clusters
            unique, counts = np.unique(labels, return_counts=True)
            if any(c < min_cluster_size for c in counts):
                return None
            
            # Métriques
            sil = silhouette_score(X, labels)
            ch = calinski_harabasz_score(X, labels)
            db = davies_bouldin_score(X, labels)
            
            return ClusteringResult(
                algorithm=f"MiniBatchKMeans_k{k}",
                n_clusters=k,
                labels=labels,
                probabilities=None,
                silhouette=sil,
                calinski_harabasz=ch,
                davies_bouldin=db,
                cluster_sizes=dict(zip(unique, counts)),
                model=model
            )
        except Exception as e:
            return None
    
    def _fit_agglomerative(self, X: np.ndarray, X_2d: np.ndarray, k: int,
                           min_cluster_size: int) -> Optional[ClusteringResult]:
        """Fit Agglomerative Clustering (clustering hiérarchique)"""
        try:
            # Limite taille pour Agglomerative (trop lent sur grand dataset)
            if len(X) > 5000:
                # Échantillonne pour accélérer
                indices = np.random.choice(len(X), 3000, replace=False)
                X_sample = X[indices]
            else:
                X_sample = X
                indices = slice(None)
            
            model = AgglomerativeClustering(n_clusters=k, linkage='ward')
            labels_sample = model.fit_predict(X_sample)
            
            # Étend aux données complètes si échantillonnage
            if isinstance(indices, np.ndarray):
                # Utilise nearest neighbors pour prédire les labels
                from sklearn.neighbors import KNeighborsClassifier
                knn = KNeighborsClassifier(n_neighbors=5)
                knn.fit(X_sample, labels_sample)
                labels = knn.predict(X)
            else:
                labels = labels_sample
            
            # Vérifie taille clusters
            unique, counts = np.unique(labels, return_counts=True)
            if any(c < min_cluster_size for c in counts):
                return None
            
            # Métriques
            sil = silhouette_score(X, labels)
            ch = calinski_harabasz_score(X, labels)
            db = davies_bouldin_score(X, labels)
            
            return ClusteringResult(
                algorithm=f"Agglomerative_k{k}",
                n_clusters=k,
                labels=labels,
                probabilities=None,
                silhouette=sil,
                calinski_harabasz=ch,
                davies_bouldin=db,
                cluster_sizes=dict(zip(unique, counts)),
                model=model
            )
        except Exception as e:
            return None
    
    def _execute_job(self, X: np.ndarray, X_2d: np.ndarray, 
                     job: Tuple[str, int, callable], min_cluster_size: int) -> Optional[ClusteringResult]:
        """
        Exécute un job de clustering (pour parallélisation)
        
        Args:
            X: Données scaled
            X_2d: Données en 2D pour viz
            job: Tuple (nom_algo, k, fonction_fit)
            min_cluster_size: Taille minimum cluster
        """
        algo_name, k, fit_func = job
        return fit_func(X, X_2d, k, min_cluster_size)
    
    def select_optimal_features(self, X: np.ndarray, feature_names: List[str], 
                                n_features: int = 20) -> Tuple[np.ndarray, List[str]]:
        """
        Sélectionne les features optimales pour le clustering
        
        Pipeline:
        1. Variance Threshold (élimine variance < 0.01)
        2. Correlation analysis (élimine corr > 0.95)
        3. SelectKBest (garde top n par ANOVA)
        """
        print(f"FEATURE SELECTION: {X.shape[1]} features -> {n_features} optimales")
        
        # 1. Variance Threshold
        selector_var = VarianceThreshold(threshold=0.01)
        X_var = selector_var.fit_transform(X)
        selected_idx_var = selector_var.get_support(indices=True)
        selected_names_var = [feature_names[i] for i in selected_idx_var]
        
        print(f"   Après variance threshold: {X_var.shape[1]} features")
        
        # 2. Correlation analysis
        if X_var.shape[1] > n_features:
            corr_matrix = np.corrcoef(X_var.T)
            upper = np.triu(corr_matrix, k=1)
            to_drop = []
            
            for i in range(len(corr_matrix)):
                if i in to_drop:
                    continue
                for j in range(i+1, len(corr_matrix)):
                    if abs(corr_matrix[i, j]) > 0.95:
                        to_drop.append(j)
            
            # Garde uniquement les features non corrélées
            keep_idx = [i for i in range(X_var.shape[1]) if i not in to_drop]
            X_corr = X_var[:, keep_idx]
            selected_names_corr = [selected_names_var[i] for i in keep_idx]
            
            print(f"   Après correlation filter: {X_corr.shape[1]} features")
        else:
            X_corr = X_var
            selected_names_corr = selected_names_var
        
        # 3. SelectKBest (si encore trop de features)
        if X_corr.shape[1] > n_features:
            # Utilise f_classif avec des labels temporaires (clustering hiérarchique rapide)
            from sklearn.cluster import KMeans
            temp_labels = KMeans(n_clusters=8, random_state=42, n_init=5).fit_predict(X_corr)
            
            selector_kbest = SelectKBest(score_func=f_classif, k=n_features)
            X_selected = selector_kbest.fit_transform(X_corr, temp_labels)
            selected_idx_kbest = selector_kbest.get_support(indices=True)
            selected_names_final = [selected_names_corr[i] for i in selected_idx_kbest]
            
            print(f"   Après SelectKBest: {X_selected.shape[1]} features")
        else:
            X_selected = X_corr
            selected_names_final = selected_names_corr
        
        print(f"   Features sélectionnées: {selected_names_final[:5]}...")
        return X_selected, selected_names_final
    
    def reduce_dimensions(self, X: np.ndarray, n_components: int = 10, 
                         method: str = 'pca') -> np.ndarray:
        """
        Réduction de dimensionnalité
        
        Args:
            X: Données
            n_components: Nombre de dimensions souhaitées
            method: 'pca' ou 'umap'
        """
        if method == 'umap' and UMAP_AVAILABLE:
            reducer = umap.UMAP(n_components=n_components, random_state=self.random_state)
        else:
            reducer = PCA(n_components=n_components, random_state=self.random_state)
        
        return reducer.fit_transform(X)
    
    def _select_best(self, results: List[ClusteringResult]) -> ClusteringResult:
        """
        Sélectionne le meilleur modèle basé sur métriques multiples
        """
        if not results:
            raise ValueError("Aucun résultat de clustering valide")
        
        # Score composite pondéré
        def composite_score(r: ClusteringResult) -> float:
            # Silhouette: [-1, 1] → normalisé [0, 1]
            sil_norm = (r.silhouette + 1) / 2
            
            # Calinski-Harabasz: > 0 → log scale
            ch_norm = min(r.calinski_harabasz / 1000, 1.0)
            
            # Davies-Bouldin: [0, ∞] → inversé, meilleur = 0
            db_norm = 1 / (1 + r.davies_bouldin)
            
            # Bonus pour GMM (probabilités) et HDBSCAN (outliers)
            algo_bonus = 0
            if r.probabilities is not None:
                algo_bonus = 0.05  # GMM
            if -1 in r.cluster_sizes:
                algo_bonus = 0.03  # HDBSCAN a des outliers
            
            return 0.4 * sil_norm + 0.3 * ch_norm + 0.2 * db_norm + 0.1 + algo_bonus
        
        best = max(results, key=composite_score)
        return best
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Prédit les clusters pour de nouveaux joueurs"""
        if self.best_result is None:
            raise ValueError("Modèle non entraîné. Appelez fit() d'abord.")
        
        X_scaled = self.scaler.transform(X)
        
        if hasattr(self.best_result.model, 'predict'):
            labels = self.best_result.model.predict(X_scaled)
        else:
            # KMeans
            labels = self.best_result.model.predict(X_scaled)
        
        # Probabilités si GMM
        probs = None
        if isinstance(self.best_result.model, GaussianMixture):
            probs = self.best_result.model.predict_proba(X_scaled)
        
        return labels, probs
    
    def get_cluster_statistics(self, X: np.ndarray, 
                               feature_names: List[str]) -> pd.DataFrame:
        """
        Calcule les statistiques par cluster
        """
        if self.best_result is None:
            raise ValueError("Modèle non entraîné")
        
        X_scaled = self.scaler.transform(X)
        labels = self.best_result.labels
        
        stats = []
        for cluster_id in sorted(set(labels)):
            if cluster_id == -1:  # Skip outliers
                continue
            
            mask = labels == cluster_id
            cluster_data = X_scaled[mask]
            
            stat = {
                'cluster_id': cluster_id,
                'n_players': mask.sum(),
                'pct_total': mask.sum() / len(labels) * 100
            }
            
            # Moyennes des features
            for i, feat in enumerate(feature_names):
                stat[f'{feat}_mean'] = cluster_data[:, i].mean()
                stat[f'{feat}_std'] = cluster_data[:, i].std()
            
            stats.append(stat)
        
        return pd.DataFrame(stats)
    
    def save(self, filepath: str):
        """Sauvegarde le modèle"""
        import joblib
        
        # Convert ClusteringResult to dict to avoid pickling issues
        def result_to_dict(r):
            return {
                'algorithm': r.algorithm,
                'n_clusters': r.n_clusters,
                'labels': r.labels,
                'probabilities': r.probabilities,
                'silhouette': r.silhouette,
                'calinski_harabasz': r.calinski_harabasz,
                'davies_bouldin': r.davies_bouldin,
                'cluster_sizes': r.cluster_sizes,
                'model': r.model
            }
        
        data = {
            'scaler': self.scaler,
            'best_result': result_to_dict(self.best_result) if self.best_result else None,
            'random_state': self.random_state
        }
        
        joblib.dump(data, filepath)
        print("OK: Modele sauvegarde: {}".format(filepath))
    
    @classmethod
    def load(cls, filepath: str):
        """Charge un modèle sauvegardé"""
        import joblib
        
        data = joblib.load(filepath)
        
        instance = cls(random_state=data['random_state'])
        instance.scaler = data['scaler']
        instance.best_result = data['best_result']
        instance.results = data['results']
        
        return instance


def find_optimal_k(X: np.ndarray, k_range: range = range(4, 16),
                   method: str = 'silhouette') -> Tuple[int, Dict]:
    """
    Trouve le k optimal avec différentes méthodes
    
    Args:
        X: Données standardisées
        k_range: Plage de k à tester
        method: 'silhouette', 'elbow', 'gap'
    """
    scores = {}
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        if method == 'silhouette':
            scores[k] = silhouette_score(X, labels)
        elif method == 'calinski':
            scores[k] = calinski_harabasz_score(X, labels)
        elif method == 'davies_bouldin':
            scores[k] = davies_bouldin_score(X, labels)
    
    # Trouve le meilleur k
    if method in ['silhouette', 'calinski']:
        best_k = max(scores, key=scores.get)
    else:  # davies_bouldin (minimiser)
        best_k = min(scores, key=scores.get)
    
    return best_k, scores


if __name__ == "__main__":
    # Test
    print("NBA-23 Auto-Clustering - Test")
    
    # Données test
    np.random.seed(42)
    X_test = np.random.randn(500, 10)
    
    # Ajoute 3 clusters artificiels
    X_test[:150] += np.array([2, 2, 0, 0, 0, 0, 0, 0, 0, 0])
    X_test[150:350] += np.array([0, 0, 2, 2, 0, 0, 0, 0, 0, 0])
    X_test[350:] += np.array([-2, -2, 0, 0, 0, 0, 0, 0, 0, 0])
    
    # Clustering
    clusterer = AutoClustering(random_state=42)
    result = clusterer.fit(X_test, k_range=range(3, 8), min_cluster_size=30)
    
    print(f"\n✓ Test réussi!")
    print(f"  Algorithme: {result.algorithm}")
    print(f"  Clusters: {result.n_clusters}")
    print(f"  Silhouette: {result.silhouette:.3f}")
