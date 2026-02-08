"""
NBA Analytics - Base Feature Engineer
Classe de base pour tous les modules de feature engineering
Évite la redondance et centralise les formules NBA
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


class BaseFeatureEngineer(ABC):
    """
    Classe de base abstraite pour tous les feature engineers du projet.
    
    Fournit:
    - Accès centralisé aux formules NBA (via NBAFormulasVectorized)
    - Normalisation automatique par 36 minutes
    - Traçabilité des features créées
    - Documentation automatique
    """
    
    def __init__(self):
        self.features_created = []
        self._feature_registry = {}
        
    @abstractmethod
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Méthode principale à implémenter par les sous-classes.
        
        Args:
            df: DataFrame avec les données brutes
            
        Returns:
            DataFrame enrichi avec les nouvelles features
        """
        pass
    
    def calculate_ts_pct(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcule le True Shooting % de manière vectorisée.
        
        TS% = PTS / (2 * (FGA + 0.44 * FTA))
        """
        pts = df.get('pts', 0)
        fga = df.get('fga', 0)
        fta = df.get('fta', 0)
        denominator = 2 * (fga + 0.44 * fta)
        return np.where(denominator > 0, pts / denominator, 0)
    
    def calculate_efg_pct(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcule l'Effective FG % de manière vectorisée.
        
        eFG% = (FGM + 0.5 * 3PM) / FGA
        """
        fgm = df.get('fgm', 0)
        fg3m = df.get('fg3m', 0)
        fga = df.get('fga', 0)
        return np.where(fga > 0, (fgm + 0.5 * fg3m) / fga, 0)
    
    def calculate_bmi(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcule l'Indice de Masse Corporelle (BMI).
        
        BMI = poids (kg) / taille (m)²
        """
        height_m = df['height_cm'] / 100
        return df['weight_kg'] / (height_m ** 2)
    
    def normalize_per_36(self, df: pd.DataFrame, stat_col: str, 
                        minutes_col: Optional[str] = None) -> pd.Series:
        """
        Normalise une statistique par 36 minutes jouées.
        
        Args:
            df: DataFrame contenant les données
            stat_col: Nom de la colonne de statistique
            minutes_col: Nom de la colonne de minutes (défaut: 'minutes' ou 'min')
            
        Returns:
            Série pandas avec la stat normalisée par 36 min
        """
        if minutes_col is None:
            minutes_col = 'minutes' if 'minutes' in df.columns else 'min'
        
        minutes = df.get(minutes_col, pd.Series([500] * len(df), index=df.index))
        minutes = minutes.replace(0, np.nan)
        
        stat = df.get(stat_col, 0)
        return (stat / minutes * 36).fillna(0)
    
    def register_feature(self, name: str, category: str, description: str) -> None:
        """
        Enregistre une feature créée pour traçabilité.
        
        Args:
            name: Nom de la feature
            category: Catégorie (ex: 'offensive', 'defensive', 'physical')
            description: Description détaillée
        """
        self._feature_registry[name] = {
            'category': category,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        self.features_created.append(name)
    
    def get_feature_documentation(self) -> pd.DataFrame:
        """
        Retourne la documentation de toutes les features créées.
        
        Returns:
            DataFrame avec les métadonnées des features
        """
        if not self._feature_registry:
            return pd.DataFrame()
        
        df = pd.DataFrame.from_dict(self._feature_registry, orient='index')
        df.index.name = 'feature_name'
        return df.reset_index()
    
    def get_feature_list(self) -> List[str]:
        """Retourne la liste des features créées."""
        return self.features_created.copy()
    
    def calculate_per_estimated(self, df: pd.DataFrame) -> pd.Series:
        """
        Estime le PER (Player Efficiency Rating) si non disponible.
        Formule simplifiée basée sur les stats disponibles.
        """
        # Composantes positives
        pts_factor = df.get('pts', 0) * 1.0
        ast_factor = df.get('ast', 0) * 0.67
        reb_factor = df.get('reb', 0) * 0.33
        stl_factor = df.get('stl', 0) * 1.5
        blk_factor = df.get('blk', 0) * 1.5
        
        # Composantes négatives
        tov_factor = df.get('tov', 0) * -0.5
        fga_factor = df.get('fga', 0) * -0.33
        fta_factor = df.get('fta', 0) * -0.15
        
        per_est = (pts_factor + ast_factor + reb_factor + 
                   stl_factor + blk_factor + tov_factor + 
                   fga_factor + fta_factor)
        
        # Normalise pour être proche de l'échelle PER standard (15 = moyenne)
        return per_est / 20
    
    def validate_dataframe(self, df: pd.DataFrame, required_cols: List[str]) -> Tuple[bool, List[str]]:
        """
        Valide qu'un DataFrame contient les colonnes requises.
        
        Returns:
            Tuple (is_valid, missing_columns)
        """
        missing = [col for col in required_cols if col not in df.columns]
        return len(missing) == 0, missing


class NBAFormulasVectorized:
    """
    Classe utilitaire statique avec toutes les formules NBA vectorisées.
    Peut être utilisée indépendamment ou via BaseFeatureEngineer.
    """
    
    @staticmethod
    def calculate_ts_pct(df: pd.DataFrame) -> pd.Series:
        """True Shooting % - vectorisé"""
        pts = df.get('pts', 0)
        fga = df.get('fga', 0)
        fta = df.get('fta', 0)
        denominator = 2 * (fga + 0.44 * fta)
        return np.where(denominator > 0, pts / denominator, 0)
    
    @staticmethod
    def calculate_efg_pct(df: pd.DataFrame) -> pd.Series:
        """Effective FG% - vectorisé"""
        fgm = df.get('fgm', 0)
        fg3m = df.get('fg3m', 0)
        fga = df.get('fga', 0)
        return np.where(fga > 0, (fgm + 0.5 * fg3m) / fga, 0)
    
    @staticmethod
    def calculate_bmi(df: pd.DataFrame) -> pd.Series:
        """BMI - vectorisé"""
        return df['weight_kg'] / ((df['height_cm'] / 100) ** 2)
    
    @staticmethod
    def calculate_ftr(df: pd.DataFrame) -> pd.Series:
        """Free Throw Rate (FTA / FGA) - vectorisé"""
        fta = df.get('fta', 0)
        fga = df.get('fga', 0)
        return np.where(fga > 0, fta / fga, 0)
    
    @staticmethod
    def calculate_3par(df: pd.DataFrame) -> pd.Series:
        """3-Point Attempt Rate (3PA / FGA) - vectorisé"""
        fg3a = df.get('fg3a', 0)
        fga = df.get('fga', 0)
        return np.where(fga > 0, fg3a / fga, 0)


if __name__ == "__main__":
    # Test rapide
    print("BaseFeatureEngineer - Test")
    
    test_data = {
        'player_id': [1, 2, 3],
        'player_name': ['Player A', 'Player B', 'Player C'],
        'height_cm': [201, 198, 211],
        'weight_kg': [102, 95, 115],
        'pts': [1500, 800, 400],
        'fga': [1200, 600, 300],
        'fta': [300, 150, 80],
        'fgm': [550, 280, 140],
        'fg3m': [150, 80, 20]
    }
    
    df_test = pd.DataFrame(test_data)
    
    # Test formules vectorisées
    formulas = NBAFormulasVectorized()
    print(f"\nTS%: {formulas.calculate_ts_pct(df_test).tolist()}")
    print(f"eFG%: {formulas.calculate_efg_pct(df_test).tolist()}")
    print(f"BMI: {formulas.calculate_bmi(df_test).tolist()}")
    
    print("\n✓ Tests passés!")
