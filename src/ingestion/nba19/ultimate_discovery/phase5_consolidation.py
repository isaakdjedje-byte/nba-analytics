#!/usr/bin/env python3
"""
NBA-19 Phase 5: Consolidation Finale

Exporte les donnees en formats utilisable:
- player_team_history_complete.json
- team_season_rosters.json
- career_summaries.json
- quality_report.json
- manual_review_queue.json

Usage:
    python phase5_consolidation.py
    
Temps: ~10 min
"""
import json
import os
from datetime import datetime
from collections import defaultdict


class ConsolidationEngine:
    """Moteur de consolidation finale"""
    
    def __init__(self):
        self.enriched = []
        self.mappings = []
        
    def load_enriched_data(self):
        """Charger donnees enrichies"""
        results_dir = "logs/nba19_discovery/results"
        
        # Enriched careers
        files = [f for f in os.listdir(results_dir) if f.startswith('enriched_careers_')]
        if not files:
            raise FileNotFoundError("Aucun fichier enrichi trouve")
        
        latest = sorted(files)[-1]
        with open(os.path.join(results_dir, latest), 'r') as f:
            data = json.load(f)
        
        self.enriched = data.get('data', [])
        print(f"[LOAD] {len(self.enriched)} carriers charges")
        
        # Extraire tous les mappings
        for career in self.enriched:
            self.mappings.extend(career.get('mappings', []))
        
        print(f"[LOAD] {len(self.mappings)} mappings extraits")
    
    def export_player_team_history(self):
        """Exporter historique joueur-equipe"""
        print("\n[EXPORT] Player team history...")
        
        # Format plat: une ligne par mapping
        history = []
        for mapping in self.mappings:
            history.append({
                'player_id': mapping['player_id'],
                'player_name': mapping['player_name'],
                'season': mapping['season'],
                'team_id': mapping['team_id'],
                'team_abbreviation': mapping['team_abbreviation'],
                'games_played': mapping.get('games_played', 0),
                'quality': mapping.get('quality', 'SILVER'),
                'confidence': mapping.get('confidence', 0.8)
            })
        
        output_dir = "data/gold/nba19"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(f"{output_dir}/player_team_history_complete.json", 'w') as f:
            json.dump({
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'total_records': len(history),
                    'version': '2.0'
                },
                'data': history
            }, f, indent=2)
        
        print(f"[OK] {len(history)} records exportes")
    
    def export_team_season_rosters(self):
        """Exporter rosters par equipe/saison"""
        print("\n[EXPORT] Team season rosters...")
        
        # Grouper par team/saison
        by_team_season = defaultdict(list)
        for m in self.mappings:
            key = (m['team_id'], m['season'])
            by_team_season[key].append({
                'player_id': m['player_id'],
                'player_name': m['player_name'],
                'games_played': m.get('games_played', 0)
            })
        
        rosters = []
        for (team_id, season), players in by_team_season.items():
            rosters.append({
                'team_id': team_id,
                'season': season,
                'roster_size': len(players),
                'players': players
            })
        
        output_dir = "data/gold/nba19"
        with open(f"{output_dir}/team_season_rosters.json", 'w') as f:
            json.dump({
                'metadata': {'total': len(rosters)},
                'data': rosters
            }, f, indent=2)
        
        print(f"[OK] {len(rosters)} rosters exportes")
    
    def export_career_summaries(self):
        """Exporter resumes de carriere"""
        print("\n[EXPORT] Career summaries...")
        
        summaries = []
        for e in self.enriched:
            summaries.append({
                'player_id': e['player_id'],
                'player_name': e['player_name'],
                'total_seasons': e['total_seasons'],
                'unique_teams': e['unique_teams'],
                'career_span': e['career_span'],
                'from_year': e['from_year'],
                'to_year': e['to_year'],
                'position': e.get('position', 'Unknown'),
                'primary_team_id': e.get('primary_team_id')
            })
        
        output_dir = "data/gold/nba19"
        with open(f"{output_dir}/career_summaries.json", 'w') as f:
            json.dump({
                'metadata': {'total': len(summaries)},
                'data': summaries
            }, f, indent=2)
        
        print(f"[OK] {len(summaries)} resumes exportes")
    
    def generate_quality_report(self):
        """Generer rapport qualite final"""
        print("\n[REPORT] Generation rapport qualite...")
        
        # Distribution qualite
        quality_dist = defaultdict(int)
        for m in self.mappings:
            quality_dist[m.get('quality', 'UNKNOWN')] += 1
        
        # Stats generales
        total_players = len(self.enriched)
        total_mappings = len(self.mappings)
        
        # Coverage
        covered_players = len(set(m['player_id'] for m in self.mappings))
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_players_in_dataset': 5103,
                'players_with_mappings': covered_players,
                'coverage_percent': covered_players / 5103 * 100,
                'total_mappings': total_mappings,
                'avg_mappings_per_player': total_mappings / covered_players if covered_players else 0
            },
            'quality_distribution': dict(quality_dist),
            'segments': {
                'GOLD': quality_dist.get('GOLD', 0),
                'SILVER': quality_dist.get('SILVER', 0),
                'BRONZE': quality_dist.get('BRONZE', 0),
                'UNKNOWN': quality_dist.get('UNKNOWN', 0)
            }
        }
        
        output_dir = "data/gold/nba19"
        with open(f"{output_dir}/quality_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n[QUALITY REPORT]")
        print(f"   Coverage: {report['summary']['coverage_percent']:.1f}%")
        print(f"   GOLD: {report['segments']['GOLD']}")
        print(f"   SILVER: {report['segments']['SILVER']}")
        print(f"   BRONZE: {report['segments']['BRONZE']}")
        
        return report
    
    def generate_manual_review_queue(self):
        """Generer liste pour review manuel"""
        print("\n[REPORT] Generation queue review manuel...")
        
        # Joueurs sans mapping ou qualite UNKNOWN
        all_player_ids = set(e['player_id'] for e in self.enriched)
        mapped_player_ids = set(m['player_id'] for m in self.mappings)
        unmapped = all_player_ids - mapped_player_ids
        
        review_queue = []
        
        # Ajouter joueurs sans mapping
        for career in self.enriched:
            if career['player_id'] in unmapped:
                review_queue.append({
                    'player_id': career['player_id'],
                    'player_name': career['player_name'],
                    'reason': 'no_mapping_found',
                    'priority': 'high' if career.get('total_seasons', 0) > 5 else 'medium'
                })
        
        # Trier par priorite et prendre top 100
        review_queue.sort(key=lambda x: x['priority'])
        top_100 = review_queue[:100]
        
        output_dir = "data/gold/nba19"
        with open(f"{output_dir}/manual_review_queue.json", 'w') as f:
            json.dump({
                'metadata': {
                    'total_need_review': len(review_queue),
                    'top_100_priority': len(top_100)
                },
                'data': top_100
            }, f, indent=2)
        
        print(f"[OK] {len(top_100)} joueurs dans queue (sur {len(review_queue)} total)")
    
    def run(self):
        """Executer consolidation complete"""
        print("="*70)
        print(">>> PHASE 5: CONSOLIDATION FINALE")
        print("="*70)
        
        self.load_enriched_data()
        self.export_player_team_history()
        self.export_team_season_rosters()
        self.export_career_summaries()
        self.generate_quality_report()
        self.generate_manual_review_queue()
        
        print("\n" + "="*70)
        print("[DONE] Phase 5 terminee!")
        print("="*70)
        print("\nLivrables crees dans: data/gold/nba19/")
        print("  - player_team_history_complete.json")
        print("  - team_season_rosters.json")
        print("  - career_summaries.json")
        print("  - quality_report.json")
        print("  - manual_review_queue.json")


def main():
    engine = ConsolidationEngine()
    engine.run()


if __name__ == "__main__":
    main()
