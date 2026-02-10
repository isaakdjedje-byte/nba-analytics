"""
Smart Prediction Filter - Système de scoring multi-critères
Étend DailyPredictionPipeline avec grading intelligent A+/A/B/C
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ml.pipeline.daily_pipeline import DailyPredictionPipeline
from utils.monitoring import get_logger, PipelineMetrics
from nba.config import get_settings

logger = get_logger(__name__)


class SmartPredictionFilter(DailyPredictionPipeline):
    """
    Pipeline de prédiction avec système de grading multi-critères.
    Étend DailyPredictionPipeline pour ajouter grading A+/A/B/C.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = get_settings()
        self.metrics = PipelineMetrics("smart_prediction_filter")
        self.confidence_thresholds = self.settings.confidence_thresholds
        self.min_games_for_confidence = self.settings.min_games_for_confidence
        
        logger.info("SmartPredictionFilter initialisé")
        logger.info(f"Seuils: {self.confidence_thresholds}")
    
    def calculate_prediction_grade(self, row: pd.Series) -> Tuple[str, float]:
        """Calcule le grade (A+/A/B/C) et le score."""
        score = 0.0
        
        # 1. Confiance modèle (40%)
        confidence = row.get('confidence', 0.5)
        score += confidence * 40
        
        # 2. Historique disponible (30%)
        season = row.get('season', '2024-25')
        if season == '2025-26':
            game_date = pd.to_datetime(row.get('game_date', '2025-10-01'))
            season_start = pd.to_datetime('2025-10-21')
            days_since_start = (game_date - season_start).days
            estimated_games = max(0, days_since_start * 3)
            history_score = min(estimated_games / self.min_games_for_confidence, 1.0)
            score += history_score * 30
        else:
            score += 30
        
        # 3. Qualité matchup (20%)
        win_pct_diff = abs(row.get('win_pct_diff', 0))
        if win_pct_diff > 0.15:
            score += 20
        elif win_pct_diff > 0.10:
            score += 15
        elif win_pct_diff > 0.05:
            score += 10
        else:
            score += 5
        
        # 4. Momentum (10%)
        momentum_diff = row.get('momentum_diff', 0)
        if abs(momentum_diff) > 1.0:
            score += 10
        elif abs(momentum_diff) > 0.5:
            score += 7
        else:
            score += 3
        
        # Grade
        if score >= 90:
            grade = 'A+'
        elif score >= 80:
            grade = 'A'
        elif score >= 70:
            grade = 'B'
        else:
            grade = 'C'
        
        return grade, score
    
    def get_recommendation(self, grade: str, confidence: float) -> str:
        """Génère recommandation PARIER/NE_PAS_PARIER."""
        if grade == 'A+' and confidence >= 0.75:
            return "PARIER"
        elif grade in ['A+', 'A'] and confidence >= 0.65:
            return "PARIER"
        elif grade == 'B' and confidence >= 0.70:
            return "PARIER_FAIBLE"
        else:
            return "NE_PAS_PARIER"
