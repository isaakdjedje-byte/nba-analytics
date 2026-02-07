"""
Orchestrateur d'enrichissement ML pour datasets GOLD.

Enrichit les joueurs avec métadonnées prédites et gère les flags de confiance.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    from .position_predictor import PositionPredictor, CareerStatusInferencer
except ImportError:
    # Fallback pour éviter les dépendances PySpark
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from position_predictor import PositionPredictor, CareerStatusInferencer

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """Résultat d'enrichissement d'un joueur."""
    player_id: int
    original_data: Dict[str, Any]
    enriched_data: Dict[str, Any]
    fields_added: List[str] = field(default_factory=list)
    fields_modified: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    enrichment_flags: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'player_id': self.player_id,
            'fields_added': self.fields_added,
            'fields_modified': self.fields_modified,
            'confidence_scores': self.confidence_scores,
            'enrichment_flags': self.enrichment_flags
        }


class SmartEnricher:
    """
    Enrichisseur intelligent pour données joueurs NBA.
    
    Enrichit les datasets GOLD avec:
    - Position prédite (K-Means)
    - Statut carrière inféré
    - Flags de confiance
    
    Usage:
        enricher = SmartEnricher()
        
        # Entraîner sur joueurs connus
        enricher.train_position_model(known_players)
        
        # Enrichir dataset
        results = enricher.enrich_dataset(players_to_enrich)
        
        # Sauvegarder modèle
        enricher.save_model("models/enricher.pkl")
    """
    
    DEFAULT_MODEL_PATH = "models/position_predictor.pkl"
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialise l'enrichisseur.
        
        Args:
            model_path: Che vers modèle sauvegardé (optionnel)
        """
        self.position_predictor = PositionPredictor()
        self.career_inferencer = CareerStatusInferencer()
        self.enrichment_stats = {
            'total_processed': 0,
            'position_predicted': 0,
            'career_inferred': 0,
            'avg_confidence': 0.0
        }
        
        # Charger modèle si disponible
        path = model_path or self.DEFAULT_MODEL_PATH
        if Path(path).exists():
            self.position_predictor.load_model(path)
            logger.info(f"Modèle chargé: {path}")
    
    def train_position_model(self, players: List[Dict], 
                            save_path: Optional[str] = None) -> bool:
        """
        Entraîne le modèle de prédiction de position.
        
        Args:
            players: Joueurs avec position connue
            save_path: Chemin de sauvegarde (optionnel)
            
        Returns:
            True si succès
        """
        success = self.position_predictor.train(players)
        
        if success and save_path:
            self.position_predictor.save_model(save_path)
        
        return success
    
    def enrich_player(self, player: Dict, 
                     predict_position: bool = True,
                     infer_career: bool = True) -> EnrichmentResult:
        """
        Enrichit un joueur avec métadonnées prédites.
        
        Args:
            player: Données joueur
            predict_position: Si True, prédit la position si manquante
            infer_career: Si True, infère le statut carrière si manquant
            
        Returns:
            EnrichmentResult avec détails
        """
        player_id = player.get('id', 0)
        original = player.copy()
        enriched = player.copy()
        
        fields_added = []
        fields_modified = []
        confidence_scores = {}
        flags = {}
        
        # 1. Prédiction position
        if predict_position and not enriched.get('position'):
            height = enriched.get('height_cm')
            weight = enriched.get('weight_kg')
            
            if height and weight:
                prediction = self.position_predictor.predict(height, weight)
                
                if prediction:
                    enriched['position'] = prediction['position']
                    enriched['position_confidence'] = prediction['confidence']
                    enriched['position_predicted'] = True
                    
                    fields_added.append('position')
                    confidence_scores['position'] = prediction['confidence']
                    flags['position_predicted'] = True
                    
                    logger.debug(f"Position prédite pour {player_id}: {prediction['position']} "
                               f"({prediction['confidence']:.1%} confiance)")
        
        # 2. Inférence statut carrière
        if infer_career and enriched.get('is_active') is None:
            from_year = enriched.get('from_year')
            to_year = enriched.get('to_year')
            
            is_active = self.career_inferencer.infer(from_year, to_year)
            
            if is_active is not None:
                enriched['is_active'] = is_active
                enriched['is_active_inferred'] = True
                
                fields_added.append('is_active')
                confidence_scores['is_active'] = 1.0  # Règle déterministe
                flags['is_active_inferred'] = True
        
        # 3. Enrichissement team_id (placeholder pour futur)
        if not enriched.get('team_id') and enriched.get('is_active'):
            # TODO: Récupérer team_id via API pour joueurs actifs
            pass
        
        return EnrichmentResult(
            player_id=player_id,
            original_data=original,
            enriched_data=enriched,
            fields_added=fields_added,
            fields_modified=fields_modified,
            confidence_scores=confidence_scores,
            enrichment_flags=flags
        )
    
    def enrich_dataset(self, players: List[Dict],
                      min_confidence: float = 0.6,
                      max_players: Optional[int] = None) -> List[EnrichmentResult]:
        """
        Enrichit un dataset complet.
        
        Args:
            players: Liste de joueurs à enrichir
            min_confidence: Confiance minimum pour inclure une prédiction
            max_players: Limite de joueurs (optionnel)
            
        Returns:
            Liste des EnrichmentResult
        """
        if not self.position_predictor.is_trained:
            logger.error("Modèle non entraîné! Appelez train_position_model() d'abord")
            return []
        
        results = []
        players_to_process = players[:max_players] if max_players else players
        
        logger.info(f"Enrichissement de {len(players_to_process)} joueurs...")
        
        for i, player in enumerate(players_to_process):
            if i % 100 == 0:
                logger.info(f"  Progression: {i}/{len(players_to_process)}")
            
            result = self.enrich_player(player)
            results.append(result)
            
            # Stats
            self.enrichment_stats['total_processed'] += 1
            if 'position' in result.fields_added:
                self.enrichment_stats['position_predicted'] += 1
            if 'is_active' in result.fields_added:
                self.enrichment_stats['career_inferred'] += 1
        
        # Calculer confiance moyenne
        all_confidences = []
        for r in results:
            all_confidences.extend(r.confidence_scores.values())
        
        if all_confidences:
            self.enrichment_stats['avg_confidence'] = sum(all_confidences) / len(all_confidences)
        
        logger.info(f"✅ Enrichissement terminé:")
        logger.info(f"  - {self.enrichment_stats['position_predicted']} positions prédites")
        logger.info(f"  - {self.enrichment_stats['career_inferred']} statuts inférés")
        logger.info(f"  - Confiance moyenne: {self.enrichment_stats['avg_confidence']:.1%}")
        
        return results
    
    def get_enriched_players(self, results: List[EnrichmentResult],
                            min_confidence: float = 0.6) -> List[Dict]:
        """
        Extrait les joueurs enrichis avec bonne confiance.
        
        Args:
            results: Résultats d'enrichissement
            min_confidence: Seuil de confiance minimum
            
        Returns:
            Liste des joueurs enrichis
        """
        enriched_players = []
        
        for result in results:
            player = result.enriched_data.copy()
            
            # Vérifier confiance position si prédite
            if player.get('position_predicted'):
                conf = result.confidence_scores.get('position', 0)
                if conf < min_confidence:
                    # Garder le joueur mais marquer comme non fiable
                    player['_position_reliable'] = False
                else:
                    player['_position_reliable'] = True
            
            enriched_players.append(player)
        
        return enriched_players
    
    def generate_report(self, results: List[EnrichmentResult]) -> Dict:
        """Génère un rapport d'enrichissement."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_players': len(results),
            'enrichment_summary': {
                'position_predicted': sum(1 for r in results if 'position' in r.fields_added),
                'career_inferred': sum(1 for r in results if 'is_active' in r.fields_added),
                'no_enrichment': sum(1 for r in results if not r.fields_added)
            },
            'confidence_distribution': {},
            'flags_distribution': {}
        }
        
        # Distribution confiance
        conf_buckets = {'high': 0, 'medium': 0, 'low': 0}
        for r in results:
            for field, conf in r.confidence_scores.items():
                if conf >= 0.8:
                    conf_buckets['high'] += 1
                elif conf >= 0.6:
                    conf_buckets['medium'] += 1
                else:
                    conf_buckets['low'] += 1
        
        report['confidence_distribution'] = conf_buckets
        
        return report
    
    def save_model(self, path: str):
        """Sauvegarde le modèle de position."""
        self.position_predictor.save_model(path)
    
    def load_model(self, path: str):
        """Charge un modèle de position."""
        self.position_predictor.load_model(path)


def enrich_gold_basic_to_premium(gold_basic_path: str,
                                 gold_premium_output: str,
                                 model_path: Optional[str] = None) -> int:
    """
    Fonction utilitaire pour enrichir GOLD Basic vers Premium.
    
    Args:
        gold_basic_path: Chemin vers players_gold_basic/players.json
        gold_premium_output: Chemin de sortie
        model_path: Modèle pré-entraîné (optionnel)
        
    Returns:
        Nombre de joueurs enrichis
    """
    # Charger GOLD Basic
    with open(gold_basic_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        players = data.get('data', data.get('players', []))
    
    logger.info(f"Chargement GOLD Basic: {len(players)} joueurs")
    
    # Initialiser enrichisseur
    enricher = SmartEnricher(model_path)
    
    # Entraîner si nécessaire (utiliser GOLD Standard comme training set)
    if not enricher.position_predictor.is_trained:
        logger.info("Entraînement du modèle sur GOLD Standard...")
        
        # Charger GOLD Standard comme training
        std_path = Path(gold_basic_path).parent.parent / 'players_gold_standard' / 'players.json'
        if std_path.exists():
            with open(std_path, 'r', encoding='utf-8') as f:
                std_data = json.load(f)
                training_players = std_data.get('data', std_data.get('players', []))
            
            enricher.train_position_model(training_players, model_path)
        else:
            logger.error("GOLD Standard non trouvé pour entraînement")
            return 0
    
    # Enrichir
    results = enricher.enrich_dataset(players, min_confidence=0.6)
    
    # Filtrer ceux qui ont au moins position + is_active
    premium_candidates = []
    for result in results:
        player = result.enriched_data
        if player.get('position') and player.get('is_active') is not None:
            premium_candidates.append(player)
    
    # Sauvegarder
    Path(gold_premium_output).parent.mkdir(parents=True, exist_ok=True)
    with open(gold_premium_output, 'w', encoding='utf-8') as f:
        json.dump({'data': premium_candidates}, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ GOLD Premium créé: {len(premium_candidates)} joueurs")
    
    # Générer rapport
    report = enricher.generate_report(results)
    report_path = Path(gold_premium_output).parent / 'enrichment_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return len(premium_candidates)


if __name__ == "__main__":
    print("Test SmartEnricher:")
    
    # Données de test
    training_data = [
        {'id': 1, 'height_cm': 191, 'weight_kg': 87, 'position': 'G'},
        {'id': 2, 'height_cm': 198, 'weight_kg': 95, 'position': 'G'},
        {'id': 3, 'height_cm': 201, 'weight_kg': 100, 'position': 'F'},
        {'id': 4, 'height_cm': 203, 'weight_kg': 104, 'position': 'F'},
        {'id': 5, 'height_cm': 211, 'weight_kg': 115, 'position': 'C'},
        {'id': 6, 'height_cm': 216, 'weight_kg': 120, 'position': 'C'},
    ]
    
    to_enrich = [
        {'id': 7, 'height_cm': 200, 'weight_kg': 98},  # Sans position
        {'id': 8, 'height_cm': 185, 'weight_kg': 85, 'from_year': 2020},  # Sans is_active
    ]
    
    enricher = SmartEnricher()
    
    # Entraîner
    if enricher.train_position_model(training_data):
        # Enrichir
        results = enricher.enrich_dataset(to_enrich)
        
        print("\nRésultats:")
        for result in results:
            print(f"\nJoueur {result.player_id}:")
            print(f"  Fields ajoutés: {result.fields_added}")
            print(f"  Confiance: {result.confidence_scores}")
            print(f"  Flags: {result.enrichment_flags}")
