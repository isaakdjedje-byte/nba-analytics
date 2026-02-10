"""
CalendarService - Service professionnel pour le calendrier NBA

Architecture:
- Indexation par date O(1)
- Cache en mémoire
- Chargement lazy
- Support multi-saisons
"""

import json
import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from nba.models.calendar import (
    CalendarMatch, CalendarDay, CalendarWeek, CalendarMonth,
    CalendarResponse, MatchStatus
)


class CalendarIndex:
    """
    Index mémoire pour accès rapide O(1) aux matchs par date.
    Structure: { "2026-02-09": [CalendarMatch, ...] }
    """
    
    def __init__(self):
        self._index: Dict[str, List[CalendarMatch]] = defaultdict(list)
        self._match_ids: Set[str] = set()  # Pour éviter les doublons
        self._loaded_dates: Set[str] = set()
        self._last_updated: Optional[datetime] = None
        
    def add_match(self, match: CalendarMatch) -> bool:
        """Ajoute un match à l'index. Retourne False si doublon."""
        if match.game_id in self._match_ids:
            return False
            
        date_key = match.game_date.isoformat()
        self._index[date_key].append(match)
        self._match_ids.add(match.game_id)
        self._loaded_dates.add(date_key)
        return True
    
    def get_by_date(self, date_key: str) -> List[CalendarMatch]:
        """Récupère les matchs d'une date spécifique O(1)"""
        return self._index.get(date_key, [])
    
    def get_by_date_range(self, start: date, end: date) -> Dict[str, List[CalendarMatch]]:
        """Récupère les matchs sur une plage de dates"""
        result = {}
        current = start
        while current <= end:
            date_key = current.isoformat()
            matches = self._index.get(date_key, [])
            if matches:
                result[date_key] = matches
            current += timedelta(days=1)
        return result
    
    def get_all_dates(self) -> List[str]:
        """Retourne toutes les dates indexées"""
        return sorted(self._index.keys())
    
    def get_date_range(self) -> Optional[Tuple[date, date]]:
        """Retourne la plage de dates couverte"""
        dates = self.get_all_dates()
        if not dates:
            return None
        return (date.fromisoformat(dates[0]), date.fromisoformat(dates[-1]))
    
    def clear(self):
        """Vide l'index"""
        self._index.clear()
        self._match_ids.clear()
        self._loaded_dates.clear()
        self._last_updated = None
    
    @property
    def count(self) -> int:
        """Nombre total de matchs indexés"""
        return len(self._match_ids)
    
    @property
    def date_count(self) -> int:
        """Nombre de dates avec matchs"""
        return len(self._loaded_dates)


class CalendarService:
    """
    Service calendrier professionnel.
    
    Features:
    - Indexation mémoire O(1)
    - Chargement par batch
    - Cache LRU pour données fréquentes
    - Multi-sources: API live, backtest, predictions
    """
    
    # Configuration
    SEASON_START = {"2025-26": date(2025, 10, 22), "2024-25": date(2024, 10, 22)}
    SEASON_END = {"2025-26": date(2026, 6, 15), "2024-25": date(2025, 6, 15)}
    
    def __init__(self, predictions_dir: str = "predictions", data_dir: str = "data/gold"):
        self.predictions_dir = Path(predictions_dir)
        self.data_dir = Path(data_dir)
        self.index = CalendarIndex()
        self._today = date.today()
        self._is_initialized = False
        
    def initialize(self, force_reload: bool = False):
        """
        Initialise le service en indexant toutes les données disponibles.
        À appeler une fois au démarrage.
        """
        if self._is_initialized and not force_reload:
            logger.info("CalendarService déjà initialisé")
            return
            
        logger.info("Initialisation CalendarService...")
        start_time = datetime.now()
        
        self.index.clear()
        
        # 1. Charger les backtests (matchs passés avec résultats)
        self._load_backtests()
        
        # 2. Charger les prédictions actuelles
        self._load_current_predictions()
        
        # 3. Indexer les matchs à venir depuis l'API
        self._load_upcoming_schedule()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"CalendarService initialisé en {elapsed:.2f}s")
        logger.info(f"  - {self.index.count} matchs indexés")
        logger.info(f"  - {self.index.date_count} dates couvertes")
        
        self._is_initialized = True
    
    def _load_backtests(self):
        """Charge les données de backtest (matchs passés avec résultats)"""
        logger.info("Chargement backtests...")
        
        backtest_files = [
            self.predictions_dir / "backtest_2024-25_detailed.csv",
            self.predictions_dir / "backtest_2025-26_detailed.csv"
        ]
        
        for file_path in backtest_files:
            if not file_path.exists():
                continue
                
            try:
                df = pd.read_csv(file_path)
                season = "2024-25" if "2024-25" in str(file_path) else "2025-26"
                
                for _, row in df.iterrows():
                    match = self._row_to_match(row, season, "backtest")
                    if match:
                        self.index.add_match(match)
                        
                logger.info(f"  ✓ {file_path.name}: {len(df)} matchs")
                
            except Exception as e:
                logger.error(f"  ✗ Erreur {file_path.name}: {e}")
    
    def _load_current_predictions(self):
        """Charge les dernières prédictions"""
        logger.info("Chargement prédictions actuelles...")
        
        # Chercher le fichier le plus récent
        pred_files = sorted(
            self.predictions_dir.glob("predictions_2*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for pred_file in pred_files[:5]:  # 5 derniers fichiers max
            try:
                with open(pred_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                predictions = data.get("predictions", [])
                for pred in predictions:
                    match = self._prediction_to_match(pred)
                    if match:
                        self.index.add_match(match)
                
                logger.info(f"  ✓ {pred_file.name}: {len(predictions)} prédictions")
                
            except Exception as e:
                logger.error(f"  ✗ Erreur {pred_file.name}: {e}")
    
    def _load_upcoming_schedule(self):
        """Charge le calendrier des matchs à venir depuis l'API NBA"""
        logger.info("Chargement calendrier à venir...")
        
        try:
            # Importer nba_api seulement si nécessaire
            from nba_api.stats.endpoints import scheduleleaguev2
            
            # Récupérer le calendrier 2025-26
            schedule = scheduleleaguev2.ScheduleLeagueV2(season="2025-26")
            games = schedule.get_normalized_dict()
            
            count = 0
            for game in games.get("Schedule", []):
                game_date = game.get("GAME_DATE")
                if not game_date:
                    continue
                    
                # Parser la date
                try:
                    dt = datetime.strptime(game_date, "%Y-%m-%d").date()
                except:
                    continue
                
                # Ne garder que les matchs futurs non encore dans l'index
                date_key = dt.isoformat()
                existing = self.index.get_by_date(date_key)
                existing_ids = {m.game_id for m in existing}
                
                game_id = str(game.get("GAME_ID", ""))
                if game_id in existing_ids:
                    continue
                
                match = CalendarMatch(
                    game_id=game_id,
                    game_date=dt,
                    game_time_us=game.get("GAME_TIME", "19:00"),
                    game_time_fr=self._us_to_fr_time(game.get("GAME_TIME", "19:00")),
                    home_team=game.get("HOME_TEAM_NAME", "Unknown"),
                    away_team=game.get("AWAY_TEAM_NAME", "Unknown"),
                    status=MatchStatus.SCHEDULED,
                    is_future=dt >= self._today,
                    data_source="api"
                )
                
                self.index.add_match(match)
                count += 1
            
            logger.info(f"  ✓ {count} matchs à venir depuis API")
            
        except ImportError:
            logger.warning("  ⚠ nba_api non disponible")
        except Exception as e:
            logger.error(f"  ✗ Erreur API: {e}")
    
    def _row_to_match(self, row: pd.Series, season: str, source: str) -> Optional[CalendarMatch]:
        """Convertit une ligne CSV en CalendarMatch"""
        try:
            # Date
            if pd.notna(row.get('game_date')):
                game_date = pd.to_datetime(row['game_date']).date()
            else:
                return None
            
            # Résultat
            was_correct = None
            actual_result = None
            if pd.notna(row.get('actual_result')):
                actual_result = row['actual_result']
                if pd.notna(row.get('prediction')):
                    was_correct = (row['prediction'] == actual_result)
            
            # Score
            home_score = int(row['home_score']) if pd.notna(row.get('home_score')) else None
            away_score = int(row['away_score']) if pd.notna(row.get('away_score')) else None
            
            # Statut
            is_past = game_date < self._today
            status = MatchStatus.FINISHED if is_past else MatchStatus.SCHEDULED
            if home_score is not None:
                status = MatchStatus.FINISHED
            
            return CalendarMatch(
                game_id=str(row.get('game_id', f"{row['home_team']}_vs_{row['away_team']}_{game_date}")),
                game_date=game_date,
                game_time_us=row.get('game_time_us', '19:00'),
                game_time_fr=row.get('game_time_fr', self._us_to_fr_time(row.get('game_time_us', '19:00'))),
                home_team=row['home_team'],
                away_team=row['away_team'],
                prediction=row.get('prediction'),
                confidence=row.get('confidence'),
                proba_home_win=row.get('proba_home_win'),
                recommendation=row.get('recommendation'),
                status=status,
                actual_result=actual_result,
                home_score=home_score,
                away_score=away_score,
                was_correct=was_correct,
                is_future=not is_past,
                data_source=source
            )
            
        except Exception as e:
            logger.error(f"Erreur conversion row: {e}")
            return None
    
    def _prediction_to_match(self, pred: dict) -> Optional[CalendarMatch]:
        """Convertit une prédiction JSON en CalendarMatch"""
        try:
            game_date = pred.get('game_date')
            if not game_date:
                return None
            
            dt = date.fromisoformat(game_date)
            is_past = dt < self._today
            
            return CalendarMatch(
                game_id=f"{pred['home_team']}_vs_{pred['away_team']}_{game_date}",
                game_date=dt,
                game_time_us=pred.get('game_time_us', '19:00'),
                game_time_fr=pred.get('game_time_fr', self._us_to_fr_time(pred.get('game_time_us', '19:00'))),
                home_team=pred['home_team'],
                away_team=pred['away_team'],
                prediction=pred.get('prediction'),
                confidence=pred.get('confidence_calibrated', pred.get('confidence')),
                proba_home_win=pred.get('proba_home_win'),
                recommendation=pred.get('recommendation_calibrated', pred.get('recommendation')),
                status=MatchStatus.FINISHED if is_past else MatchStatus.SCHEDULED,
                is_future=not is_past,
                data_source="prediction"
            )
            
        except Exception as e:
            logger.error(f"Erreur conversion prediction: {e}")
            return None
    
    @staticmethod
    def _us_to_fr_time(time_us: str) -> str:
        """Convertit heure US en heure France (+6h)"""
        try:
            hour, minute = map(int, time_us.split(':'))
            fr_hour = (hour + 6) % 24
            return f"{fr_hour:02d}:{minute:02d}"
        except:
            return "01:00"
    
    @staticmethod
    def _get_french_day_name(dt: date) -> str:
        """Nom du jour en français"""
        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        return days[dt.weekday()]
    
    @staticmethod
    def _get_french_month_name(month: int) -> str:
        """Nom du mois en français"""
        months = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        return months[month - 1]
    
    # =========================================================================
    # API Publique
    # =========================================================================
    
    def get_day(self, date_key: str) -> Optional[CalendarDay]:
        """
        Récupère un jour spécifique avec tous ses matchs.
        Complexité: O(1) grâce à l'index
        """
        if not self._is_initialized:
            self.initialize()
        
        try:
            dt = date.fromisoformat(date_key)
        except:
            return None
        
        matches = self.index.get_by_date(date_key)
        
        if not matches:
            # Retourner un jour vide
            return CalendarDay(
                date=dt,
                day_name=self._get_french_day_name(dt),
                day_number=dt.day,
                month=dt.month,
                year=dt.year,
                match_count=0,
                is_today=(dt == self._today),
                is_past=(dt < self._today)
            )
        
        # Calculer stats
        completed = [m for m in matches if m.status == MatchStatus.FINISHED]
        correct = [m for m in completed if m.was_correct]
        has_preds = any(m.prediction for m in matches)
        
        confidences = [m.confidence for m in matches if m.confidence is not None]
        avg_conf = sum(confidences) / len(confidences) if confidences else None
        
        return CalendarDay(
            date=dt,
            day_name=self._get_french_day_name(dt),
            day_number=dt.day,
            month=dt.month,
            year=dt.year,
            match_count=len(matches),
            matches=sorted(matches, key=lambda m: m.game_time_us),
            has_predictions=has_preds,
            completed_matches=len(completed),
            correct_predictions=len(correct) if correct else None,
            accuracy=(len(correct) / len(completed)) if completed else None,
            avg_confidence=avg_conf,
            is_today=(dt == self._today),
            is_weekend=dt.weekday() >= 5,
            is_past=(dt < self._today)
        )
    
    def get_days_range(self, start: date, end: date) -> List[CalendarDay]:
        """
        Récupère une plage de jours.
        Complexité: O(n) où n = nombre de jours
        """
        if not self._is_initialized:
            self.initialize()
        
        days = []
        current = start
        while current <= end:
            day = self.get_day(current.isoformat())
            if day:
                days.append(day)
            current += timedelta(days=1)
        return days
    
    def get_week(self, date_key: str) -> List[CalendarDay]:
        """
        Récupère la semaine contenant une date (Lundi-Dimanche).
        """
        try:
            dt = date.fromisoformat(date_key)
        except:
            dt = self._today
        
        # Trouver le lundi de la semaine
        monday = dt - timedelta(days=dt.weekday())
        
        # Retourner les 7 jours
        return self.get_days_range(monday, monday + timedelta(days=6))
    
    def get_month(self, year: int, month: int) -> List[CalendarDay]:
        """
        Récupère tous les jours d'un mois.
        """
        start = date(year, month, 1)
        
        # Dernier jour du mois
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        
        return self.get_days_range(start, end)
    
    def get_calendar_response(
        self,
        view_mode: str = "month",
        target_date: Optional[date] = None,
        season: str = "2025-26"
    ) -> CalendarResponse:
        """
        Génère une réponse calendrier complète.
        
        Args:
            view_mode: "day", "week", ou "month"
            target_date: Date cible (défaut: aujourd'hui)
            season: Saison NBA
        """
        if not self._is_initialized:
            self.initialize()
        
        target = target_date or self._today
        
        # Déterminer la plage de dates
        if view_mode == "day":
            days = [self.get_day(target.isoformat())]
            start, end = target, target
            has_prev = self._has_matches_on_date(target - timedelta(days=1))
            has_next = self._has_matches_on_date(target + timedelta(days=1))
            
        elif view_mode == "week":
            days = self.get_week(target.isoformat())
            start = days[0].date if days else target
            end = days[-1].date if days else target
            has_prev = True  # Toujours permettre navigation
            has_next = True
            
        else:  # month
            days = self.get_month(target.year, target.month)
            start = date(target.year, target.month, 1)
            if target.month == 12:
                end = date(target.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(target.year, target.month + 1, 1) - timedelta(days=1)
            has_prev = True
            has_next = True
        
        # Calculer stats globales
        total_matches = sum(d.match_count for d in days)
        with_preds = sum(1 for d in days if d.has_predictions)
        completed = sum(d.completed_matches for d in days)
        
        # Accuracy globale
        all_correct = sum((d.correct_predictions or 0) for d in days)
        all_completed = sum(d.completed_matches for d in days)
        overall_acc = (all_correct / all_completed) if all_completed > 0 else None
        
        # Date précédente/suivante avec matchs
        prev_date = self._find_nearest_date_with_matches(target, -1) if has_prev else None
        next_date = self._find_nearest_date_with_matches(target, 1) if has_next else None
        
        return CalendarResponse(
            season=season,
            view_mode=view_mode,
            start_date=start,
            end_date=end,
            today=self._today,
            days=[d for d in days if d is not None],
            current_day=self.get_day(target.isoformat()) if view_mode == "day" else None,
            total_matches=total_matches,
            matches_with_predictions=with_preds,
            matches_completed=completed,
            overall_accuracy=overall_acc,
            has_previous=has_prev,
            has_next=has_next,
            previous_date=prev_date.isoformat() if prev_date else None,
            next_date=next_date.isoformat() if next_date else None,
            data_sources=["backtest", "prediction", "api"]
        )
    
    def _has_matches_on_date(self, dt: date) -> bool:
        """Vérifie si des matchs existent sur une date"""
        return len(self.index.get_by_date(dt.isoformat())) > 0
    
    def _find_nearest_date_with_matches(self, from_date: date, direction: int) -> Optional[date]:
        """Trouve la date la plus proche avec des matchs"""
        current = from_date + timedelta(days=direction)
        max_days = 30  # Limite de recherche
        
        for _ in range(max_days):
            if self._has_matches_on_date(current):
                return current
            current += timedelta(days=direction)
        
        return None
    
    def get_season_stats(self, season: str = "2025-26") -> dict:
        """Statistiques globales de la saison"""
        if not self._is_initialized:
            self.initialize()
        
        date_range = self.index.get_date_range()
        if not date_range:
            return {"error": "Aucune donnée"}
        
        all_matches = []
        current = date_range[0]
        while current <= date_range[1]:
            all_matches.extend(self.index.get_by_date(current.isoformat()))
            current += timedelta(days=1)
        
        completed = [m for m in all_matches if m.was_correct is not None]
        correct = [m for m in completed if m.was_correct]
        
        return {
            "season": season,
            "total_matches": len(all_matches),
            "completed_matches": len(completed),
            "correct_predictions": len(correct),
            "accuracy": len(correct) / len(completed) if completed else 0,
            "date_range": {
                "start": date_range[0].isoformat(),
                "end": date_range[1].isoformat()
            },
            "coverage_days": self.index.date_count
        }


# Singleton pour réutilisation
_calendar_service: Optional[CalendarService] = None


def get_calendar_service() -> CalendarService:
    """Retourne le singleton CalendarService"""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService()
        _calendar_service.initialize()
    return _calendar_service
