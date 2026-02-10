"""Service layer for predictions endpoint and legacy week view compatibility."""

from collections import defaultdict
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Optional
import json


logger = logging.getLogger(__name__)


def _latest_predictions_file(predictions_dir: Path) -> Optional[Path]:
    dated_files = sorted(predictions_dir.glob("predictions_2*.json"), reverse=True)
    optimized_files = sorted(predictions_dir.glob("predictions_optimized_*.json"), reverse=True)
    if dated_files:
        return dated_files[0]
    if optimized_files:
        return optimized_files[0]
    return None


def _in_date_range(game_date: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> bool:
    if not game_date:
        return start_date is None and end_date is None
    if start_date and game_date < start_date:
        return False
    if end_date and game_date > end_date:
        return False
    return True


def _filter_predictions(
    raw_predictions: list[dict[str, Any]],
    min_confidence: float,
    team: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    team_lower = team.lower() if team else None

    for pred in raw_predictions:
        confidence = pred.get("confidence_calibrated", pred.get("confidence", 0))
        if confidence < min_confidence:
            continue

        game_date = pred.get("game_date")
        if not _in_date_range(game_date, start_date, end_date):
            continue

        if team_lower:
            home = pred.get("home_team", "").lower()
            away = pred.get("away_team", "").lower()
            if team_lower not in home and team_lower not in away:
                continue

        filtered.append(
            {
                "home_team": pred.get("home_team"),
                "away_team": pred.get("away_team"),
                "prediction": pred.get("prediction"),
                "proba_home_win": pred.get("proba_home_win"),
                "confidence": confidence,
                "recommendation": pred.get("recommendation_calibrated", pred.get("recommendation", "SKIP")),
                "game_date": pred.get("game_date"),
                "game_time_us": pred.get("game_time_us"),
                "game_time_fr": pred.get("game_time_fr"),
            }
        )

    return filtered


def _build_legacy_week_response(filtered: list[dict[str, Any]], min_confidence: float, team: Optional[str]) -> dict[str, Any]:
    grouped_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pred in filtered:
        date_key = pred.get("game_date") or datetime.now().strftime("%Y-%m-%d")
        grouped_by_date[date_key].append(pred)

    sorted_dates = sorted(grouped_by_date.keys())
    days: list[dict[str, Any]] = []
    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    for date_key in sorted_dates:
        day_predictions = grouped_by_date[date_key]
        dt = datetime.strptime(date_key, "%Y-%m-%d")
        avg_conf = round(sum(item["confidence"] for item in day_predictions) / len(day_predictions), 3) if day_predictions else 0
        days.append(
            {
                "date": date_key,
                "day_name": day_names[dt.weekday()],
                "match_count": len(day_predictions),
                "avg_confidence": avg_conf,
                "matches": day_predictions,
            }
        )

    week_start = sorted_dates[0] if sorted_dates else datetime.now().strftime("%Y-%m-%d")
    week_end = sorted_dates[-1] if sorted_dates else week_start

    return {
        "week_range": {"start": week_start, "end": week_end},
        "days": days,
        "total_matches": len(filtered),
        "high_confidence_count": sum(1 for item in filtered if item["confidence"] >= 0.7),
        "avg_confidence": round(sum(item["confidence"] for item in filtered) / len(filtered), 3) if filtered else 0,
        "view": "week",
        "filters_applied": {
            "min_confidence": min_confidence,
            "team": team,
        },
    }


def get_predictions_response(
    view: str = "day",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_confidence: float = 0.0,
    team: Optional[str] = None,
    predictions_dir: str = "predictions",
) -> dict[str, Any]:
    base_dir = Path(predictions_dir)
    latest_file = _latest_predictions_file(base_dir)
    if not latest_file:
        logger.info("No predictions file found in %s", base_dir)
        return {"predictions": [], "count": 0, "date": None, "view": view}

    with open(latest_file, encoding="utf-8") as handle:
        payload = json.load(handle)

    raw_predictions = payload.get("predictions", [])
    if not isinstance(raw_predictions, list):
        raise ValueError("Invalid predictions payload: 'predictions' must be a list")

    filtered = _filter_predictions(raw_predictions, min_confidence, team, start_date, end_date)

    if view == "week":
        return _build_legacy_week_response(filtered, min_confidence, team)

    return {
        "predictions": filtered,
        "count": len(filtered),
        "date": payload.get("timestamp"),
        "view": view,
        "pagination": {
            "total": len(filtered),
            "page": 1,
            "per_page": len(filtered),
        },
    }
