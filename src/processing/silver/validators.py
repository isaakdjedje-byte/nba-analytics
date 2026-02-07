"""
Validateurs pour la couche Silver.

Règles de validation configurables pour 3 niveaux:
- all: Validation legere (20% nulls max) - Dataset historique complet
- intermediate: Validation medium (10% nulls max) - Joueurs 2000-2016
- contemporary: Validation stricte (5% nulls max) - Joueurs 2016+ pour ML
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .stratification import load_stratification_config, get_validation_config

logger = logging.getLogger(__name__)


class SilverValidator:
    """
    Validateur configurable pour les données Silver.
    
    Supporte 3 niveaux de validation via configuration YAML:
    - all: Dataset historique complet (seuil 20%)
    - intermediate: Joueurs 2000-2016 (seuil 10%)
    - contemporary: Joueurs 2016+ (seuil 5%)
    
    Args:
        level: Niveau de validation ('all', 'intermediate', 'contemporary')
        config: Configuration de stratification (chargee si None)
    """
    
    def __init__(self, level: str = 'contemporary', config: Optional[Dict[str, Any]] = None):
        """
        Initialise le validateur avec niveau specifique.
        
        Args:
            level: Niveau de validation ('all', 'intermediate', 'contemporary')
            config: Configuration deja chargee (optionnel)
        """
        self.level = level
        self.config = config or load_stratification_config()
        self.level_config = get_validation_config(level, self.config)
        
        self.errors = []
        self.warnings = []  # HOTFIX: Ajoute pour eviter AttributeError
        self.stats = {
            'total': 0,
            'duplicates': 0,
            'null_cells': 0,
            'total_cells': 0
        }
        
        logger.info(f"Validateur initialise: level='{level}', "
                   f"seuil_nulls={self.level_config.get('null_threshold', 0.05):.0%}")
    
    def validate(self, players: List[Dict]) -> bool:
        """
        Valide les donnees Silver selon le niveau configure.
        
        Args:
            players: Liste des joueurs nettoyes
            
        Returns:
            True si validation OK
        """
        logger.info(f"Validation Silver [{self.level}]: {len(players)} joueurs")
        
        self.errors = []
        self.stats['total'] = len(players)
        
        checks = [
            self._check_no_duplicates(players),
            self._check_critical_fields(players),
            self._check_ranges(players),
            self._check_null_rate(players),
        ]
        
        if all(checks):
            logger.info(f"Validation Silver [{self.level}] OK")
            return True
        else:
            logger.error(f"Validation Silver [{self.level}] echouee: {len(self.errors)} erreurs")
            for error in self.errors[:5]:  # Limiter l'affichage
                logger.error(f"  - {error}")
            return False
    
    def _check_no_duplicates(self, players: List[Dict]) -> bool:
        """Vérifie l'absence de doublons."""
        ids = [p.get('id') for p in players]
        unique_ids = set(ids)
        
        if len(ids) != len(unique_ids):
            self.stats['duplicates'] = len(ids) - len(unique_ids)
            self.errors.append(f"{self.stats['duplicates']} doublons détectés")
            return False
        return True
    
    def _check_critical_fields(self, players: List[Dict]) -> bool:
        """Vérifie les champs critiques selon le niveau de validation."""
        # Utilise les champs requis definis dans la configuration
        critical = self.level_config.get('required_fields', ['id', 'full_name'])
        
        missing_count = 0
        for player in players:
            for field in critical:
                if not player.get(field):
                    missing_count += 1
                    if missing_count <= 5:  # Limiter les logs
                        self.errors.append(
                            f"Champ critique '{field}' manquant pour ID {player.get('id')}"
                        )
        
        # En mode 'all', on accepte des champs manquants (historique incomplet)
        if self.level == 'all':
            if missing_count > 0:
                logger.warning(f"{missing_count} champs critiques manquants (acceptable en mode 'all')")
            return True
        
        return missing_count == 0
    
    def _check_ranges(self, players: List[Dict]) -> bool:
        """Vérifie les plages de valeurs."""
        ranges = {
            'height_cm': (160, 240),
            'weight_kg': (60, 160),
            'age': (18, 45),
        }
        
        for player in players:
            for field, (min_val, max_val) in ranges.items():
                value = player.get(field)
                if value is not None:
                    if not (min_val <= value <= max_val):
                        self.warnings.append(
                            f"{player.get('full_name')}: {field}={value} "
                            f"hors plage [{min_val}, {max_val}]"
                        )
        return True
    
    def _check_null_rate(self, players: List[Dict]) -> bool:
        """Vérifie le taux de nulls global selon le seuil du niveau."""
        total_cells = 0
        null_cells = 0
        
        for player in players:
            for value in player.values():
                total_cells += 1
                if value is None:
                    null_cells += 1
        
        self.stats['total_cells'] = total_cells
        self.stats['null_cells'] = null_cells
        
        if total_cells == 0:
            self.errors.append("Aucune donnee")
            return False
        
        null_rate = null_cells / total_cells
        threshold = self.level_config.get('null_threshold', 0.05)
        
        logger.info(f"Taux nulls Silver ({self.level}): {null_rate:.1%} (seuil: {threshold:.0%})")
        
        if null_rate > threshold:
            self.errors.append(
                f"Taux nulls trop eleve: {null_rate:.1%} (max {threshold:.0%})"
            )
            return False
        
        return True
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de validation."""
        return {
            **self.stats,
            'null_rate': self.stats['null_cells'] / max(self.stats['total_cells'], 1),
            'error_count': len(self.errors)
        }


if __name__ == "__main__":
    print("Test SilverValidator avec niveaux:")
    
    # Test data - joueur complet
    test_player_full = {
        'id': 1, 'full_name': 'LeBron James', 'height_cm': 206, 
        'weight_kg': 113, 'position': 'F', 'is_active': True
    }
    
    # Test data - joueur incomplet (simule historique)
    test_player_partial = {
        'id': 2, 'full_name': 'Old Player'  # Manque height, weight, position
    }
    
    print("\n1. Test niveau 'all' (accepte incomplet):")
    validator_all = SilverValidator(level='all')
    result = validator_all.validate([test_player_full, test_player_partial])
    print(f"   Resultat: {result}")
    
    print("\n2. Test niveau 'contemporary' (strict):")
    validator_modern = SilverValidator(level='contemporary')
    result = validator_modern.validate([test_player_full])
    print(f"   Resultat: {result}")
    
    print("\n3. Test niveau 'contemporary' avec joueur incomplet:")
    result = validator_modern.validate([test_player_partial])
    print(f"   Resultat: {result} (attendu: False)")
