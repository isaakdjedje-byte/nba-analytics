"""
Models Pydantic pour le calendrier NBA
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import date as DateType, datetime as DateTimeType
from enum import Enum


class MatchStatus(str, Enum):
    """Statut d'un match"""
    SCHEDULED = "scheduled"      # Programmé
    LIVE = "live"               # En cours
    FINISHED = "finished"       # Terminé
    POSTPONED = "postponed"     # Reporté


class CalendarMatch(BaseModel):
    """Match unifié pour le calendrier (passé ou futur)"""
    # Identification
    game_id: str = Field(..., description="ID unique du match")
    game_date: DateType = Field(..., description="Date du match")
    
    # Horaires
    game_time_us: str = Field(..., description="Heure US (format HH:MM)")
    game_time_fr: str = Field(..., description="Heure France (format HH:MM)")
    
    # Équipes
    home_team: str = Field(..., description="Équipe à domicile")
    away_team: str = Field(..., description="Équipe à l'extérieur")
    
    # Prédictions ML (null pour matchs très futurs)
    prediction: Optional[str] = Field(None, description="Prédiction: 'Home Win' ou 'Away Win'")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confiance (0-1)")
    proba_home_win: Optional[float] = Field(None, ge=0, le=1, description="Probabilité victoire domicile")
    recommendation: Optional[str] = Field(None, description="Recommandation: HIGH_CONFIDENCE, etc.")
    
    # Résultats réels (pour matchs passés)
    status: MatchStatus = Field(MatchStatus.SCHEDULED, description="Statut du match")
    actual_result: Optional[str] = Field(None, description="Résultat réel: 'home_win' ou 'away_win'")
    home_score: Optional[int] = Field(None, description="Score équipe domicile")
    away_score: Optional[int] = Field(None, description="Score équipe extérieure")
    was_correct: Optional[bool] = Field(None, description="La prédiction était-elle correcte?")
    
    # Métadonnées
    is_future: bool = Field(True, description="True si match à venir")
    data_source: str = Field("api", description="Source: 'api', 'backtest', 'prediction'")
    
    model_config = ConfigDict(
        json_encoders={DateType: lambda v: v.isoformat()}
    )


class CalendarDay(BaseModel):
    """Jour du calendrier avec tous ses matchs"""
    date: DateType = Field(..., description="Date du jour")
    day_name: str = Field(..., description="Nom du jour en français")
    day_number: int = Field(..., ge=1, le=31, description="Numéro du jour")
    month: int = Field(..., ge=1, le=12, description="Mois (1-12)")
    year: int = Field(..., description="Année")
    
    # Matchs
    match_count: int = Field(0, ge=0, description="Nombre de matchs")
    matches: List[CalendarMatch] = Field(default_factory=list, description="Liste des matchs")
    
    # Statistiques
    has_predictions: bool = Field(False, description="Au moins une prédiction disponible")
    completed_matches: int = Field(0, ge=0, description="Matchs terminés")
    correct_predictions: Optional[int] = Field(None, description="Prédictions correctes")
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="Accuracy du jour")
    avg_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confiance moyenne")
    
    # UI
    is_today: bool = Field(False, description="C'est aujourd'hui")
    is_weekend: bool = Field(False, description="Week-end")
    is_past: bool = Field(False, description="Jour passé")
    
    model_config = ConfigDict(
        json_encoders={DateType: lambda v: v.isoformat()}
    )


class CalendarWeek(BaseModel):
    """Semaine du calendrier"""
    week_number: int = Field(..., ge=1, le=53, description="Numéro de semaine")
    start_date: DateType = Field(..., description="Lundi de la semaine")
    end_date: DateType = Field(..., description="Dimanche de la semaine")
    days: List[CalendarDay] = Field(default_factory=list, description="7 jours")
    
    # Stats
    total_matches: int = Field(0, ge=0)
    has_predictions_count: int = Field(0, ge=0)
    completed_count: int = Field(0, ge=0)
    week_accuracy: Optional[float] = Field(None, ge=0, le=1)
    
    model_config = ConfigDict(
        json_encoders={DateType: lambda v: v.isoformat()}
    )


class CalendarMonth(BaseModel):
    """Mois du calendrier"""
    year: int = Field(..., description="Année")
    month: int = Field(..., ge=1, le=12, description="Mois")
    month_name: str = Field(..., description="Nom du mois en français")
    weeks: List[CalendarWeek] = Field(default_factory=list)
    
    # Stats
    total_matches: int = Field(0, ge=0)
    days_with_matches: int = Field(0, ge=0)
    month_accuracy: Optional[float] = Field(None, ge=0, le=1)


class CalendarResponse(BaseModel):
    """Réponse complète du calendrier"""
    # Contexte
    season: str = Field(..., description="Saison (ex: 2025-26)")
    view_mode: str = Field("month", description="Mode: 'day', 'week', 'month'")
    
    # Période
    start_date: DateType = Field(..., description="Date de début")
    end_date: DateType = Field(..., description="Date de fin")
    today: DateType = Field(..., description="Date du jour")
    
    # Données
    days: List[CalendarDay] = Field(default_factory=list, description="Jours demandés")
    weeks: Optional[List[CalendarWeek]] = Field(None, description="Semaines (si view=month)")
    current_day: Optional[CalendarDay] = Field(None, description="Jour sélectionné")
    
    # Stats globales
    total_matches: int = Field(0, ge=0)
    matches_with_predictions: int = Field(0, ge=0)
    matches_completed: int = Field(0, ge=0)
    overall_accuracy: Optional[float] = Field(None, ge=0, le=1)
    
    # Pagination
    has_previous: bool = Field(False, description="Page précédente disponible")
    has_next: bool = Field(False, description="Page suivante disponible")
    previous_date: Optional[str] = Field(None, description="Date page précédente")
    next_date: Optional[str] = Field(None, description="Date page suivante")
    
    # Métadonnées
    generated_at: DateTimeType = Field(default_factory=DateTimeType.now)
    data_sources: List[str] = Field(default_factory=list, description="Sources utilisées")
    
    model_config = ConfigDict(
        json_encoders={
            DateType: lambda v: v.isoformat(),
            DateTimeType: lambda v: v.isoformat()
        }
    )


class DateRangeRequest(BaseModel):
    """Requête pour une plage de dates"""
    start_date: DateType
    end_date: DateType
    include_history: bool = Field(True, description="Inclure résultats passés")
    include_upcoming: bool = Field(True, description="Inclure matchs à venir")


class DayDetailResponse(BaseModel):
    """Détail d'un jour spécifique"""
    day: CalendarDay
    previous_day: Optional[str] = Field(None, description="Date jour précédent avec matchs")
    next_day: Optional[str] = Field(None, description="Date jour suivant avec matchs")
    season_context: Dict = Field(default_factory=dict, description="Contexte saison")
