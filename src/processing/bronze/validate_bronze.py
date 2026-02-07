"""
Validation des données Bronze.

Vérifie la qualité des données brutes avant transformation Silver.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class BronzeValidator:
    """
    Validateur pour la couche Bronze.
    
    Vérifie:
    - Présence des champs obligatoires
    - Cohérence des IDs
    - Pas de doublons
    - Taux de complétion minimum
    """
    
    def __init__(self, min_completion_rate: float = 0.3):
        """
        Initialise le validateur.
        
        Args:
            min_completion_rate: Taux minimum de champs remplis (30% pour Bronze)
        """
        self.min_completion_rate = min_completion_rate
        self.errors = []
        self.warnings = []
    
    def validate(self, players: List[Dict]) -> bool:
        """
        Valide un ensemble de données Bronze.
        
        Args:
            players: Liste des joueurs Bronze
            
        Returns:
            True si validation OK, False sinon
        """
        logger.info(f"Validation Bronze: {len(players)} joueurs")
        
        self.errors = []
        self.warnings = []
        
        # Vérifications
        checks = [
            self._check_not_empty(players),
            self._check_ids_unique(players),
            self._check_required_fields(players),
            self._check_completion_rate(players),
        ]
        
        if all(checks):
            logger.info("✅ Validation Bronze OK")
            return True
        else:
            logger.error(f"❌ Validation Bronze échouée: {len(self.errors)} erreurs")
            for error in self.errors:
                logger.error(f"  - {error}")
            return False
    
    def _check_not_empty(self, players: List[Dict]) -> bool:
        """Vérifie que la liste n'est pas vide."""
        if not players:
            self.errors.append("Liste de joueurs vide")
            return False
        return True
    
    def _check_ids_unique(self, players: List[Dict]) -> bool:
        """Vérifie l'unicité des IDs."""
        ids = [p.get('id') for p in players]
        if len(ids) != len(set(ids)):
            duplicates = len(ids) - len(set(ids))
            self.errors.append(f"{duplicates} IDs dupliqués")
            return False
        return True
    
    def _check_required_fields(self, players: List[Dict]) -> bool:
        """Vérifie les champs obligatoires."""
        required = ['id', 'full_name']
        
        for player in players:
            for field in required:
                if not player.get(field):
                    self.errors.append(f"Champ '{field}' manquant pour joueur {player.get('id')}")
                    return False
        return True
    
    def _check_completion_rate(self, players: List[Dict]) -> bool:
        """Vérifie le taux de complétion minimum."""
        total_fields = 0
        filled_fields = 0
        
        for player in players:
            for key, value in player.items():
                total_fields += 1
                if value is not None and value != '':
                    filled_fields += 1
        
        if total_fields == 0:
            self.errors.append("Aucun champ trouvé")
            return False
        
        completion_rate = filled_fields / total_fields
        
        if completion_rate < self.min_completion_rate:
            self.errors.append(
                f"Taux de complétion trop faible: {completion_rate:.1%} "
                f"(minimum {self.min_completion_rate:.0%})"
            )
            return False
        
        logger.info(f"Taux de complétion Bronze: {completion_rate:.1%}")
        return True
    
    def get_report(self) -> Dict:
        """Retourne un rapport de validation."""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


if __name__ == "__main__":
    print("Test BronzeValidator:")
    validator = BronzeValidator()
    
    # Test avec données vides
    result = validator.validate([])
    print(f"Validation vide: {result}")
    print(f"Erreurs: {validator.errors}")
