#!/usr/bin/env python3
"""
NBA-19 Phase 4: Enrichissement

Ajoute du contexte metier:
- Career summaries (saisons, equipes, duree)
- Position inference
- Geographic context
- Data lineage

Usage:
    python phase4_enrichment.py
    
Temps: ~20 min
"""
import json
import os
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


class EnrichmentEngine:
    """Moteur d'enrichissement des donnees"""
    
    def __init__(self):
        self.mappings = []
        self.enriched = []
        
    def load_validated_mappings(self):
        """Charger mappings valides"""
        results_dir = "logs/nba19_discovery/results"
        
        files = [f for f in os.listdir(results_dir) if f.startswith('validated_mappings_')]
        if not files:
            raise FileNotFoundError("Aucun fichier de mappings valides trouve")
        
        latest = sorted(files)[-1]
        filepath = os.path.join(results_dir, latest)
        
        print(f"[LOAD] Chargement: {latest}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.mappings = data.get('data', [])
        print(f"[OK] {len(self.mappings)} mappings charges")
    
    def enrich_career_summaries(self):
        """Enrichir avec resumes de carriere"""
        print("\n[ENRICH] Generation resumes de carriere...")
        
        # Grouper par joueur
        by_player = defaultdict(list)
        for m in self.mappings:
            by_player[m['player_id']].append(m)
        
        enriched = []
        for player_id, mappings in by_player.items():
            player_name = mappings[0]['player_name']
            
            # Calculer stats carriere
            seasons = set(m['season'] for m in mappings)
            teams = set(m['team_id'] for m in mappings)
            
            # Trouver equipe principale (plus de saisons)
            team_counts = defaultdict(int)
            for m in mappings:
                team_counts[m['team_id']] += 1
            primary_team = max(team_counts.items(), key=lambda x: x[1])[0] if team_counts else None
            
            # Annees debut/fin
            season_years = []
            for s in seasons:
                try:
                    year = int(s.split('-')[0])
                    season_years.append(year)
                except:
                    pass
            
            from_year = min(season_years) if season_years else None
            to_year = max(season_years) if season_years else None
            
            career_summary = {
                'player_id': player_id,
                'player_name': player_name,
                'total_seasons': len(seasons),
                'unique_teams': len(teams),
                'team_ids': list(teams),
                'primary_team_id': primary_team,
                'career_span': f"{from_year}-{to_year}" if from_year and to_year else None,
                'from_year': from_year,
                'to_year': to_year,
                'mappings': mappings
            }
            
            enriched.append(career_summary)
        
        self.enriched = enriched
        print(f"[OK] {len(enriched)} resumes generes")
        
        return enriched
    
    def infer_positions(self):
        """Infere les positions si manquantes"""
        print("\n[ENRICH] Inference des positions...")
        
        # Charger donnees joueurs originales
        with open("data/silver/players_advanced/players.json", 'r', encoding='utf-8') as f:
            players_data = json.load(f)
        
        player_info = {p['id']: p for p in players_data.get('data', [])}
        
        inferred_count = 0
        for summary in self.enriched:
            player_id = summary['player_id']
            player = player_info.get(player_id, {})
            
            # Si position existe deja
            if player.get('position'):
                summary['position'] = player['position']
                summary['position_source'] = 'original_data'
            else:
                # Inference simple par pattern
                height = player.get('height_cm', 0)
                if height > 210:
                    summary['position'] = 'C'
                    summary['position_source'] = 'inferred_height'
                elif height > 200:
                    summary['position'] = 'F'
                    summary['position_source'] = 'inferred_height'
                elif height > 0:
                    summary['position'] = 'G'
                    summary['position_source'] = 'inferred_height'
                else:
                    summary['position'] = 'Unknown'
                    summary['position_source'] = 'unknown'
                
                inferred_count += 1
        
        print(f"[OK] {inferred_count} positions inferees")
    
    def add_data_lineage(self):
        """Ajoute metadata de lineage"""
        print("\n[ENRICH] Ajout metadata lineage...")
        
        for summary in self.enriched:
            summary['data_lineage'] = {
                'discovered_at': datetime.now().isoformat(),
                'discovery_version': '2.0',
                'validation_status': 'validated',
                'enriched_at': datetime.now().isoformat()
            }
    
    def save_enriched(self):
        """Sauvegarder donnees enrichies"""
        output_dir = "logs/nba19_discovery/results"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Format complet
        with open(f"{output_dir}/enriched_careers_{timestamp}.json", 'w') as f:
            json.dump({
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'total_players': len(self.enriched),
                    'version': '2.0'
                },
                'data': self.enriched
            }, f, indent=2)
        
        # Format simplifie pour export
        simplified = []
        for e in self.enriched:
            simplified.append({
                'player_id': e['player_id'],
                'player_name': e['player_name'],
                'total_seasons': e['total_seasons'],
                'unique_teams': e['unique_teams'],
                'career_span': e['career_span'],
                'position': e.get('position', 'Unknown'),
                'primary_team_id': e.get('primary_team_id')
            })
        
        with open(f"{output_dir}/career_summaries_{timestamp}.json", 'w') as f:
            json.dump({
                'metadata': {'total': len(simplified)},
                'data': simplified
            }, f, indent=2)
        
        print(f"\n[SAVE] {len(self.enriched)} carriers enrichies sauvegardees")
    
    def run(self):
        """Executer enrichissement complet"""
        print("="*70)
        print(">>> PHASE 4: ENRICHISSEMENT")
        print("="*70)
        
        self.load_validated_mappings()
        self.enrich_career_summaries()
        self.infer_positions()
        self.add_data_lineage()
        self.save_enriched()
        
        print("\n[DONE] Phase 4 terminee!")


def main():
    engine = EnrichmentEngine()
    engine.run()


if __name__ == "__main__":
    main()
