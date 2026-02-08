"""
NBA-19 Phase 1: Pre-validation et Segmentation

Analyse les 5 103 joueurs et les segmente en 3 cohortes:
- Segment A (GOLD): api_cached + roster + csv (priorite 1)
- Segment B (SILVER): imputed avec season data (priorite 2)
- Segment C (BRONZE): imputed sans season data (priorite 3)
"""
import json
import os
from typing import Dict, List, Tuple
from collections import defaultdict


class PlayerSegmenter:
    """Segmente les joueurs selon la qualite des donnees disponibles"""
    
    def __init__(self, players_file: str):
        self.players_file = players_file
        self.players = []
        self.segments = {
            'A': [],  # GOLD
            'B': [],  # SILVER
            'C': []   # BRONZE
        }
    
    def load_players(self) -> int:
        """Charger les joueurs depuis le fichier JSON"""
        print(f"[FILE] Chargement: {self.players_file}")
        
        with open(self.players_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.players = data.get('data', [])
        print(f"[OK] {len(self.players)} joueurs charges")
        return len(self.players)
    
    def segment_players(self):
        """Segmenter les joueurs selon la qualite des donnees"""
        print("\n[SCAN] Analyse et segmentation...")
        
        for player in self.players:
            player_id = player.get('id')
            data_source = player.get('data_source', 'unknown')
            
            # Criteres de segmentation
            has_from_year = player.get('from_year') is not None
            has_position = player.get('position') is not None
            has_birth_date = player.get('birth_date') is not None
            
            # Segment A: GOLD (api_cached, roster, csv avec metadonnees)
            if data_source in ['api_cached', 'roster', 'csv']:
                if has_from_year or has_position:
                    self.segments['A'].append(player)
                    continue
            
            # Segment B: SILVER (imputed avec season ou metadonnees)
            if data_source == 'imputed':
                if has_position or has_birth_date:
                    self.segments['B'].append(player)
                    continue
            
            # Segment C: BRONZE (reste)
            self.segments['C'].append(player)
        
        self._print_summary()
    
    def _print_summary(self):
        """Afficher le resume de la segmentation"""
        print("\n" + "=" * 60)
        print("[STATS] RESULTATS DE LA SEGMENTATION")
        print("=" * 60)
        
        total = sum(len(s) for s in self.segments.values())
        
        for segment, players in self.segments.items():
            tier = {'A': 'GOLD', 'B': 'SILVER', 'C': 'BRONZE'}[segment]
            pct = (len(players) / total * 100) if total > 0 else 0
            
            print(f"\n[TARGET] Segment {segment} ({tier}): {len(players)} joueurs ({pct:.1f}%)")
            
            # Echantillon
            if players:
                sample = players[:3]
                print("   Echantillon:")
                for p in sample:
                    src = p.get('data_source', 'unknown')
                    name = p.get('full_name', 'Unknown')
                    print(f"   - {name} (source: {src})")
        
        print("\n" + "=" * 60)
    
    def save_segments(self, output_dir: str):
        """Sauvegarder les segments dans des fichiers JSON"""
        os.makedirs(output_dir, exist_ok=True)
        
        for segment, players in self.segments.items():
            tier = {'A': 'gold', 'B': 'silver', 'C': 'bronze'}[segment]
            filepath = os.path.join(output_dir, f'segment_{segment}_{tier}.json')
            
            data = {
                'metadata': {
                    'segment': segment,
                    'tier': tier,
                    'total_players': len(players),
                    'created_at': self._get_timestamp()
                },
                'data': players
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"[SAVE] Segment {segment} sauvegarde: {filepath}")
    
    def get_top_players_for_test(self, segment: str, limit: int = 100) -> List[Dict]:
        """
        Obtenir les N premiers joueurs d'un segment pour test
        
        Args:
            segment: 'A', 'B', ou 'C'
            limit: Nombre de joueurs (defaut: 100)
            
        Returns:
            Liste des joueurs
        """
        players = self.segments.get(segment, [])
        return players[:limit]
    
    def _get_timestamp(self) -> str:
        """Obtenir le timestamp actuel"""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Point d'entree principal"""
    print("=" * 60)
    print("[SCAN] NBA-19 PHASE 1: PRE-VALIDATION ET SEGMENTATION")
    print("=" * 60)
    
    # Configuration
    players_file = "data/silver/players_advanced/players.json"
    output_dir = "logs/nba19_discovery/segments"
    
    # Creer le segmenteur
    segmenter = PlayerSegmenter(players_file)
    
    # Charger et segmenter
    count = segmenter.load_players()
    segmenter.segment_players()
    
    # Sauvegarder
    segmenter.save_segments(output_dir)
    
    # Afficher recommandation
    print("\n[DONE] Phase 1 terminee!")
    print(f"\n[TARGET] Pour le test (100 joueurs), je recommande:")
    print(f"   Segment A (GOLD): {min(100, len(segmenter.segments['A']))} joueurs")
    print(f"   -> Qualite optimale, API fiable")
    
    print("\n[FOLDER] Prochaine etape:")
    print(f"   python phase2_discovery_engine.py --segment A --limit 100")


if __name__ == "__main__":
    main()
