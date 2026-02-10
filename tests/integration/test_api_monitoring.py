"""Post-release backend monitoring checks (A8)."""

import logging
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import nba.api.main as api_main


client = TestClient(api_main.app)


class TestMonitoringStatusPaths:
    def test_422_path_has_request_id(self):
        response = client.post(
            "/api/v1/export",
            data="not json",
            headers={"Content-Type": "application/json", "X-Request-ID": "a8-422"},
        )
        assert response.status_code == 422
        assert response.headers.get("X-Request-ID") == "a8-422"

    def test_503_path_has_request_id(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: False)
        monkeypatch.setattr(api_main.betting_service, "availability_error", lambda: "betting backend unavailable")

        response = client.get("/api/v1/bets/stats", headers={"X-Request-ID": "a8-503"})
        assert response.status_code == 503
        assert response.headers.get("X-Request-ID") == "a8-503"
        assert response.json().get("detail") == "betting backend unavailable"

    def test_500_path_has_request_id(self, monkeypatch: pytest.MonkeyPatch):
        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("predictions service unavailable")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        response = client.get("/api/v1/predictions", headers={"X-Request-ID": "a8-500"})
        assert response.status_code == 500
        assert response.headers.get("X-Request-ID") == "a8-500"
        assert response.json().get("detail") == "predictions service unavailable"


class TestMonitoringLogs:
    def test_request_completed_log_contains_observable_fields(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger="nba.api.main"):
            response = client.get("/health", headers={"X-Request-ID": "a8-log"})

        assert response.status_code == 200
        request_logs = [r for r in caplog.records if r.getMessage() == "Request completed"]
        assert request_logs
        record = request_logs[-1]
        assert getattr(record, "request_id", None) == "a8-log"
        assert getattr(record, "path", None) == "/health"
        assert getattr(record, "status_code", None) == 200
