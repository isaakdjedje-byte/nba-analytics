"""Service layer for analysis endpoints."""

import logging
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)


def _find_column(dataframe: pd.DataFrame, candidates: list[str]) -> str:
    for column in candidates:
        if column in dataframe.columns:
            return column
    raise KeyError(candidates[0])


def temporal_analysis() -> dict[str, Any]:
    try:
        dataframe = pd.read_csv("predictions/backtest_2025-26_detailed.csv")
        prediction_col = _find_column(dataframe, ["prediction", "predicted", "predicted_result"])
        actual_col = _find_column(dataframe, ["actual_result", "actual", "winner"])

        dataframe = dataframe.sort_values("game_date")
        dataframe["match_count"] = range(1, len(dataframe) + 1)

        segments: list[dict[str, Any]] = []
        ranges = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 9999)]

        for start, end in ranges:
            mask = (dataframe["match_count"] > start) & (dataframe["match_count"] <= end)
            segment_df = dataframe[mask]
            if len(segment_df) == 0:
                continue

            correct = (segment_df[prediction_col] == segment_df[actual_col]).sum()
            accuracy = correct / len(segment_df)
            recommendation = "MOYEN"
            if accuracy > 0.65:
                recommendation = "OPTIMAL"
            elif accuracy < 0.55:
                recommendation = "ATTENDRE"

            segments.append(
                {
                    "range": f"{start}-{end if end < 9999 else '+'}",
                    "matches_count": len(segment_df),
                    "accuracy": round(accuracy, 4),
                    "recommendation": recommendation,
                }
            )

        optimal = max(segments, key=lambda item: item["accuracy"]) if segments else None
        return {
            "segments": segments,
            "optimal_threshold": 100 if optimal and optimal["range"].startswith("100") else 150,
            "current_season_progress": f"{len(dataframe)} matchs analyses",
            "overall_accuracy": round((dataframe[prediction_col] == dataframe[actual_col]).mean(), 4),
        }

    except Exception as exc:
        logger.exception("Temporal analysis failed")
        return {"error": str(exc), "segments": []}
