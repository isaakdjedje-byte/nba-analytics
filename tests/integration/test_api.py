"""Integration and contract-regression tests for FastAPI API v1."""

from pathlib import Path
from types import SimpleNamespace
import sys
import logging

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import nba.api.main as api_main


client = TestClient(api_main.app)


def _route_map() -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in api_main.app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not path or not methods:
            continue
        if path in {"/", "/health"} or path.startswith("/api/v1"):
            for method in methods:
                if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    routes.add((method, path))
    return routes


class TestAPIRoot:
    def test_api_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        data = response.json()
        assert data["message"] == "NBA Analytics API"
        assert isinstance(data["version"], str)

    def test_health_check_contract(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        data = response.json()
        assert data["status"] == "healthy"
        assert isinstance(data["environment"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["timestamp"], str)


class TestAPIContractFreezeV1:
    def test_registered_v1_routes_are_stable(self):
        expected = {
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/api/v1/datasets"),
            ("GET", "/api/v1/datasets/{dataset_name}"),
            ("POST", "/api/v1/export"),
            ("POST", "/api/v1/catalog/scan"),
            ("GET", "/api/v1/predictions"),
            ("POST", "/api/v1/bets"),
            ("POST", "/api/v1/bets/update"),
            ("GET", "/api/v1/bets"),
            ("GET", "/api/v1/bets/stats"),
            ("GET", "/api/v1/analysis/temporal"),
            ("GET", "/api/v1/calendar/today"),
            ("GET", "/api/v1/calendar/date/{date_str}"),
            ("GET", "/api/v1/calendar/day/{date_str}"),
            ("GET", "/api/v1/calendar/month/{year}/{month}"),
            ("GET", "/api/v1/calendar/week/{date_str}"),
            ("GET", "/api/v1/calendar/range"),
            ("GET", "/api/v1/calendar/matches/{date_str}"),
            ("GET", "/api/v1/calendar/stats/{season}"),
            ("GET", "/api/v1/calendar/seasons"),
            ("POST", "/api/v1/calendar/refresh"),
        }
        assert _route_map() == expected


class TestPredictionsNonRegression:
    def test_predictions_day_payload_contract(self, monkeypatch: pytest.MonkeyPatch):
        payload = {
            "predictions": [
                {
                    "home_team": "Boston Celtics",
                    "away_team": "New York Knicks",
                    "prediction": "Home Win",
                    "proba_home_win": 0.74,
                    "confidence": 0.79,
                    "recommendation": "HIGH_CONFIDENCE",
                    "game_date": "2026-02-10",
                    "game_time_us": "19:00",
                    "game_time_fr": "01:00",
                }
            ],
            "count": 1,
            "date": "2026-02-10T11:00:00",
            "view": "day",
            "pagination": {"total": 1, "page": 1, "per_page": 1},
        }

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", lambda **_: payload)

        response = client.get("/api/v1/predictions?view=day&min_confidence=0.7")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"predictions", "count", "date", "view", "pagination"}
        assert data["view"] == "day"
        assert data["count"] == 1
        assert isinstance(data["predictions"], list)
        assert data["predictions"][0]["home_team"] == "Boston Celtics"

    def test_predictions_week_legacy_payload_contract(self, monkeypatch: pytest.MonkeyPatch):
        payload = {
            "week_range": {"start": "2026-02-10", "end": "2026-02-16"},
            "days": [
                {
                    "date": "2026-02-10",
                    "day_name": "Mardi",
                    "match_count": 2,
                    "avg_confidence": 0.71,
                    "matches": [],
                }
            ],
            "total_matches": 2,
            "high_confidence_count": 1,
            "avg_confidence": 0.71,
            "view": "week",
            "filters_applied": {"min_confidence": 0.6, "team": None},
        }

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", lambda **_: payload)

        response = client.get("/api/v1/predictions?view=week&min_confidence=0.6")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {
            "week_range",
            "days",
            "total_matches",
            "high_confidence_count",
            "avg_confidence",
            "view",
            "filters_applied",
        }
        assert data["view"] == "week"
        assert "start" in data["week_range"] and "end" in data["week_range"]

    def test_predictions_internal_error_path(self, monkeypatch: pytest.MonkeyPatch):
        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("predictions service unavailable")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        response = client.get("/api/v1/predictions")
        assert response.status_code == 500
        assert "X-Request-ID" in response.headers
        assert response.json()["detail"] == "predictions service unavailable"


class TestBettingRoutes:
    def test_betting_routes_success_when_backend_available(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: True)
        monkeypatch.setattr(api_main.betting_service, "get_stats", lambda: {"total_bets": 2, "win_rate": 0.5})
        monkeypatch.setattr(
            api_main.betting_service,
            "get_bets",
            lambda status, limit: [
                SimpleNamespace(
                    id="bet_1",
                    date="2026-02-10",
                    match="Celtics vs Knicks",
                    prediction="Home Win",
                    stake=25.0,
                    odds=1.85,
                    result="pending",
                    profit=None,
                )
            ],
        )

        stats_resp = client.get("/api/v1/bets/stats")
        list_resp = client.get("/api/v1/bets?status=all&limit=50")

        assert stats_resp.status_code == 200
        assert stats_resp.json()["total_bets"] == 2

        assert list_resp.status_code == 200
        body = list_resp.json()
        assert "bets" in body
        assert isinstance(body["bets"], list)
        assert body["bets"][0]["id"] == "bet_1"

    def test_betting_routes_return_503_when_backend_unavailable(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: False)
        monkeypatch.setattr(api_main.betting_service, "availability_error", lambda: "betting backend unavailable")

        stats_resp = client.get("/api/v1/bets/stats")
        create_resp = client.post(
            "/api/v1/bets",
            json={
                "date": "2026-02-10",
                "match": "Celtics vs Knicks",
                "prediction": "Home Win",
                "stake": 25.0,
                "odds": 1.85,
            },
        )

        assert stats_resp.status_code == 503
        assert "X-Request-ID" in stats_resp.headers
        assert stats_resp.json()["detail"] == "betting backend unavailable"
        assert create_resp.status_code == 503
        assert "X-Request-ID" in create_resp.headers

    def test_503_mode_does_not_impact_other_routes(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: False)
        monkeypatch.setattr(api_main.betting_service, "availability_error", lambda: "betting backend unavailable")
        monkeypatch.setattr(
            api_main.predictions_service,
            "get_predictions_response",
            lambda **_: {"predictions": [], "count": 0, "date": None, "view": "day", "pagination": {"total": 0, "page": 1, "per_page": 0}},
        )

        health_resp = client.get("/health")
        pred_resp = client.get("/api/v1/predictions")

        assert health_resp.status_code == 200
        assert pred_resp.status_code == 200
        assert pred_resp.json()["view"] == "day"

    def test_create_bet_rejects_negative_stake(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: True)

        response = client.post(
            "/api/v1/bets",
            json={
                "date": "2026-02-10",
                "match": "Celtics vs Knicks",
                "prediction": "Home Win",
                "stake": -5,
                "odds": 1.85,
            },
        )

        assert response.status_code == 400
        assert "X-Request-ID" in response.headers
        assert response.json()["detail"] == "stake must be >= 0"

    def test_create_bet_rejects_odds_below_one(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: True)

        response = client.post(
            "/api/v1/bets",
            json={
                "date": "2026-02-10",
                "match": "Celtics vs Knicks",
                "prediction": "Home Win",
                "stake": 25,
                "odds": 0.95,
            },
        )

        assert response.status_code == 400
        assert "X-Request-ID" in response.headers
        assert response.json()["detail"] == "odds must be >= 1"


class TestAnalysisTemporal:
    def test_temporal_analysis_uses_predicted_actual_columns(self):
        response = client.get("/api/v1/analysis/temporal")
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data
        assert "overall_accuracy" in data
        assert "error" not in data

    def test_temporal_analysis_error_path(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(api_main.analysis_service, "temporal_analysis", lambda: {"error": "boom", "segments": []})
        response = client.get("/api/v1/analysis/temporal")
        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "boom"
        assert data["segments"] == []


class TestAPIErrorHandling:
    def test_invalid_json_payload(self):
        response = client.post(
            "/api/v1/export",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
        assert "X-Request-ID" in response.headers
        assert "detail" in response.json()

    def test_endpoint_not_found(self):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


class TestObservabilityHardening:
    def test_request_id_is_propagated_when_provided(self):
        request_id = "orch-a7-test-id"
        response = client.get("/health", headers={"X-Request-ID": request_id})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == request_id

    def test_request_completion_log_is_emitted(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger="nba.api.main"):
            response = client.get("/health", headers={"X-Request-ID": "orch-a7-log-test"})

        assert response.status_code == 200
        messages = [record.getMessage() for record in caplog.records]
        assert any("Request completed" in message for message in messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
