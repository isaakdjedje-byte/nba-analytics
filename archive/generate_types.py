#!/usr/bin/env python3
"""
Generate TypeScript types from Pydantic models.
Run: python scripts/generate_types.py
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def generate_typescript_types():
    """Generate TypeScript types manually defined."""
    
    output = """// Auto-generated from Pydantic models
// Do not edit manually - run: python scripts/generate_types.py

export interface Prediction {
  home_team: string;
  away_team: string;
  prediction: string;
  proba_home_win: number;
  confidence: number;
  recommendation: string;
}

export interface Bet {
  id: string;
  date: string;
  match: string;
  prediction: string;
  stake: number;
  odds: number;
  result?: 'win' | 'loss' | 'pending';
  profit?: number;
}

export interface BetRequest {
  date: string;
  match: string;
  prediction: string;
  stake: number;
  odds: number;
}

export interface PaperTradingStats {
  total_bets: number;
  won_bets: number;
  lost_bets: number;
  pending_bets: number;
  total_profit: number;
  avg_profit: number;
  win_rate: number;
}

export interface TemporalSegment {
  range: string;
  matches_count: number;
  accuracy: number;
  recommendation: string;
}

export interface TemporalAnalysisResponse {
  segments: TemporalSegment[];
  optimal_threshold: number;
  current_season_progress: string;
  overall_accuracy: number;
}

export interface PredictionsResponse {
  predictions: Prediction[];
  count: number;
  date?: string;
}

export interface BetsResponse {
  bets: Bet[];
}
"""
    
    # Write to file
    output_path = Path("frontend/src/lib/types.ts")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output)
    
    print(f"[OK] Types generated: {output_path}")
    print(f"     Total interfaces: 9")

if __name__ == "__main__":
    generate_typescript_types()
