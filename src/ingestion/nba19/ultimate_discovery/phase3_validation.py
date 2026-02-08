#!/usr/bin/env python3
"""
NBA-19 Phase 3: Validation Multi-Source

Valide les mappings decouverts:
- Cross-validation avec rosters 2018-2024 (ground truth)
- Detection des incoherences
- Quality scoring final

Usage:
    python phase3_validation.py
    
Temps: ~15 min
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict


class ValidationEngine:
    """Moteur de validation des mappings"""
    
    def __init__(self):
        self.mappings = []
        self.validation_results = []
        self.ground_truth = {}  # Roster 2018-2024
        
    def load_discovered_mappings(self):
        """Charger les mappings de Phase 2"""
        results_dir = "logs/nba19_discovery/results"
        
        # Trouver le fichier le plus recent
        files = [f for f in os.listdir(results_dir) if f.startswith('all_mappings_')]
        if not files:
            raise FileNotFoundError("Aucun fichier de mappings trouve")
        
        latest = sorted(files)[-1]
        filepath = os.path.join(results_dir, latest)
        
        print(f"[LOAD] Chargement: {latest}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.mappings = data.get('data', [])
        print(f"[OK] {len(self.mappings)} mappings charges")
    
    def load_ground_truth(self):
        """Charger les rosters 2018-2024 comme verite terrain"""
        rosters_dir = "data/raw/rosters/historical"
        
        print("\n[LOAD] Chargement rosters 2018-2024 (ground truth)...")
        
        for filename in os.listdir(rosters_dir):
            if not filename.startswith('rosters_') or not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(rosters_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            season = data['metadata']['season']
            
            for team in data.get('data', []):
                team_id = team['team_id']
                
                for player in team.get('players', []):
                    player_id = player.get('PLAYER_ID')
                    if player_id:
                        key = (player_id, season)
                        self.ground_truth[key] = {
                            'team_id': team_id,
                            'team_name': team['team_name'],
                            'player_name': player.get('PLAYER', 'Unknown')
                        }
        
        print(f"[OK] {len(self.ground_truth)} references chargees")
    
    def validate_mappings(self):
        """Valider tous les mappings"""
        print("\n[VALIDATION] Validation des mappings...")
        
        validated = []
        issues = []
        
        # Grouper par joueur
        by_player = defaultdict(list)
        for m in self.mappings:
            by_player[m['player_id']].append(m)
        
        total = len(by_player)
        for idx, (player_id, mappings) in enumerate(by_player.items(), 1):
            if idx % 500 == 0:
                print(f"   {idx}/{total} joueurs valides...")
            
            player_name = mappings[0]['player_name']
            
            # Valider chaque mapping
            for mapping in mappings:
                validation = self._validate_single(mapping)
                
                if validation['status'] == 'ok':
                    validated.append({**mapping, **validation})
                else:
                    issues.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'mapping': mapping,
                        'issue': validation
                    })
        
        print(f"\n[OK] Validation terminee:")
        print(f"   Valides: {len(validated)}")
        print(f"   Problemes: {len(issues)}")
        
        return validated, issues
    
    def _validate_single(self, mapping: Dict) -> Dict:
        """Valider un mapping individuel"""
        player_id = mapping['player_id']
        season = mapping['season']
        discovered_team = mapping['team_id']
        
        # Check 1: Ground truth (si disponible)
        key = (player_id, season)
        if key in self.ground_truth:
            expected_team = self.ground_truth[key]['team_id']
            if discovered_team == expected_team:
                return {
                    'status': 'ok',
                    'quality': 'GOLD',
                    'confidence': 1.0,
                    'validation': 'ground_truth_verified'
                }
            else:
                return {
                    'status': 'mismatch',
                    'quality': 'SILVER',
                    'confidence': 0.5,
                    'validation': 'ground_truth_mismatch',
                    'expected_team': expected_team
                }
        
        # Check 2: Format saison valide
        if not self._is_valid_season(season):
            return {
                'status': 'invalid',
                'quality': 'BRONZE',
                'confidence': 0.3,
                'validation': 'invalid_season_format'
            }
        
        # Check 3: Team ID valide
        if not self._is_valid_team_id(discovered_team):
            return {
                'status': 'invalid',
                'quality': 'BRONZE',
                'confidence': 0.3,
                'validation': 'invalid_team_id'
            }
        
        # Default: OK mais pas verifie
        return {
            'status': 'ok',
            'quality': 'SILVER',
            'confidence': 0.8,
            'validation': 'api_verified'
        }
    
    def _is_valid_season(self, season: str) -> bool:
        """Verifier format saison"""
        if not season or len(season) != 7:
            return False
        try:
            parts = season.split('-')
            if len(parts) != 2:
                return False
            year1 = int(parts[0])
            year2 = int(parts[1])
            return 1946 <= year1 <= 2025 and 0 <= year2 <= 99
        except:
            return False
    
    def _is_valid_team_id(self, team_id: int) -> bool:
        """Verifier team ID valide"""
        # NBA team IDs sont dans la plage 1610612700 - 1610612800
        return 1610612700 <= team_id <= 1610612800
    
    def generate_quality_report(self, validated: List, issues: List):
        """Generer rapport qualite"""
        print("\n[REPORT] Generation rapport qualite...")
        
        quality_dist = defaultdict(int)
        for v in validated:
            quality_dist[v['quality']] += 1
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_mappings': len(validated) + len(issues),
                'validated': len(validated),
                'issues': len(issues),
                'quality_distribution': dict(quality_dist)
            },
            'quality_distribution': dict(quality_dist),
            'issues_sample': issues[:20]  # Premieres 20 issues
        }
        
        output_dir = "logs/nba19_discovery/results"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f"{output_dir}/validation_report_{timestamp}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[OK] Rapport sauvegarde")
        print("\n[DISTRIBUTION QUALITE]")
        for tier, count in sorted(quality_dist.items()):
            pct = count / len(validated) * 100 if validated else 0
            print(f"   {tier}: {count} ({pct:.1f}%)")
        
        return report
    
    def save_validated_mappings(self, validated: List):
        """Sauvegarder mappings valides"""
        output_dir = "logs/nba19_discovery/results"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f"{output_dir}/validated_mappings_{timestamp}.json", 'w') as f:
            json.dump({
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'total': len(validated)
                },
                'data': validated
            }, f, indent=2)
        
        print(f"[SAVE] {len(validated)} mappings valides sauvegardes")
    
    def run(self):
        """Executer validation complete"""
        print("="*70)
        print(">>> PHASE 3: VALIDATION MULTI-SOURCE")
        print("="*70)
        
        self.load_discovered_mappings()
        self.load_ground_truth()
        
        validated, issues = self.validate_mappings()
        self.generate_quality_report(validated, issues)
        self.save_validated_mappings(validated)
        
        print("\n[DONE] Phase 3 terminee!")


def main():
    engine = ValidationEngine()
    engine.run()


if __name__ == "__main__":
    main()
