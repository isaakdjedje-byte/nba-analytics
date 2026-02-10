"""
Router API pour le calendrier NBA
Endpoints RESTful pour accès calendrier
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional, List
import logging

from nba.services.calendar_service import get_calendar_service
from nba.models.calendar import (
    CalendarResponse, CalendarDay, CalendarMatch
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/today", response_model=CalendarResponse)
def get_today_calendar(
    view_mode: str = Query("day", description="Mode: day, week, month")
):
    """
    Récupère le calendrier pour aujourd'hui.
    Parfait pour l'affichage initial du dashboard.
    """
    try:
        service = get_calendar_service()
        response = service.get_calendar_response(
            view_mode=view_mode,
            target_date=date.today()
        )
        return response
    except Exception as e:
        logger.error(f"Erreur get_today_calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/date/{date_str}", response_model=CalendarResponse)
def get_calendar_by_date(
    date_str: str,
    view_mode: str = Query("day", description="Mode: day, week, month"),
    season: str = Query("2025-26", description="Saison NBA")
):
    """
    Récupère le calendrier pour une date spécifique.
    
    Args:
        date_str: Date au format YYYY-MM-DD
        view_mode: Vue jour, semaine ou mois
        season: Saison (2025-26 par défaut)
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    
    try:
        service = get_calendar_service()
        response = service.get_calendar_response(
            view_mode=view_mode,
            target_date=target_date,
            season=season
        )
        return response
    except Exception as e:
        logger.error(f"Erreur get_calendar_by_date: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/day/{date_str}", response_model=CalendarDay)
def get_day_detail(date_str: str):
    """
    Récupère le détail d'un jour spécifique avec tous ses matchs.
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    
    try:
        service = get_calendar_service()
        day = service.get_day(date_str)
        
        if day is None:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée trouvée pour le {date_str}"
            )
        
        return day
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_day_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/month/{year}/{month}", response_model=CalendarResponse)
def get_month_calendar(
    year: int,
    month: int,
    season: str = Query("2025-26", description="Saison NBA")
):
    """
    Récupère le calendrier complet d'un mois.
    
    Exemple: /calendar/month/2026/2 pour février 2026
    """
    if not (1 <= month <= 12):
        raise HTTPException(
            status_code=400,
            detail="Le mois doit être entre 1 et 12"
        )
    
    try:
        service = get_calendar_service()
        target_date = date(year, month, 1)
        response = service.get_calendar_response(
            view_mode="month",
            target_date=target_date,
            season=season
        )
        return response
    except Exception as e:
        logger.error(f"Erreur get_month_calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/week/{date_str}", response_model=CalendarResponse)
def get_week_calendar(
    date_str: str,
    season: str = Query("2025-26", description="Saison NBA")
):
    """
    Récupère le calendrier de la semaine contenant une date.
    La semaine va du lundi au dimanche.
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    
    try:
        service = get_calendar_service()
        response = service.get_calendar_response(
            view_mode="week",
            target_date=target_date,
            season=season
        )
        return response
    except Exception as e:
        logger.error(f"Erreur get_week_calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/range", response_model=CalendarResponse)
def get_calendar_range(
    start: str = Query(..., description="Date début (YYYY-MM-DD)"),
    end: str = Query(..., description="Date fin (YYYY-MM-DD)"),
    season: str = Query("2025-26", description="Saison NBA")
):
    """
    Récupère le calendrier pour une plage de dates personnalisée.
    """
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="La date de début doit être avant la date de fin"
        )
    
    # Limite à 31 jours pour performance
    if (end_date - start_date).days > 31:
        raise HTTPException(
            status_code=400,
            detail="La plage maximale est de 31 jours"
        )
    
    try:
        service = get_calendar_service()
        days = service.get_days_range(start_date, end_date)
        
        # Calculer stats
        total_matches = sum(d.match_count for d in days)
        completed = sum(d.completed_matches for d in days)
        correct = sum((d.correct_predictions or 0) for d in days)
        
        return CalendarResponse(
            season=season,
            view_mode="custom",
            start_date=start_date,
            end_date=end_date,
            today=date.today(),
            days=days,
            total_matches=total_matches,
            matches_completed=completed,
            overall_accuracy=(correct / completed) if completed > 0 else None,
            has_previous=True,
            has_next=True
        )
    except Exception as e:
        logger.error(f"Erreur get_calendar_range: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches/{date_str}", response_model=List[CalendarMatch])
def get_matches_by_date(date_str: str):
    """
    Récupère uniquement les matchs d'une date (sans métadonnées jour).
    Plus léger que /day/{date}.
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    
    try:
        service = get_calendar_service()
        day = service.get_day(date_str)
        return day.matches if day else []
    except Exception as e:
        logger.error(f"Erreur get_matches_by_date: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{season}")
def get_season_stats(season: str = "2025-26"):
    """
    Statistiques globales de la saison.
    """
    try:
        service = get_calendar_service()
        stats = service.get_season_stats(season)
        return stats
    except Exception as e:
        logger.error(f"Erreur get_season_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seasons")
def get_available_seasons():
    """
    Liste les saisons disponibles.
    """
    return {
        "seasons": ["2024-25", "2025-26"],
        "current": "2025-26",
        "upcoming": "2026-27"
    }


@router.post("/refresh")
def refresh_calendar_data():
    """
    Force le rechargement des données calendrier.
    Utile après ajout de nouvelles prédictions.
    """
    try:
        service = get_calendar_service()
        service.initialize(force_reload=True)
        return {
            "status": "success",
            "message": "Données calendrier rechargées",
            "matches_indexed": service.index.count,
            "dates_covered": service.index.date_count
        }
    except Exception as e:
        logger.error(f"Erreur refresh_calendar_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
