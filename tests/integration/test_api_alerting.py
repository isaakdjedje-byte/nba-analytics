"""Alerting and incident drill checks for backend observability (A9)."""

import logging
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import nba.api.main as api_main


client = TestClient(api_main.app)


class TestAlertingSignals:
    def test_422_below_threshold_is_not_alerted(self, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()
        with caplog.at_level(logging.INFO, logger="nba.api.main"):
            response = client.post(
                "/api/v1/export",
                data="not json",
                headers={"Content-Type": "application/json", "X-Request-ID": "a12-422-low"},
            )

        assert response.status_code == 422
        detected = [r for r in caplog.records if r.getMessage() == "Alert condition detected"]
        observed = [r for r in caplog.records if r.getMessage() == "Alert condition observed (below threshold)"]
        assert not detected
        assert observed
        record = observed[-1]
        assert getattr(record, "request_id", None) == "a12-422-low"
        assert getattr(record, "status_code", None) == 422

    def test_422_threshold_triggers_alert(self, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()
        with caplog.at_level(logging.WARNING, logger="nba.api.main"):
            for i in range(5):
                response = client.post(
                    "/api/v1/export",
                    data="not json",
                    headers={"Content-Type": "application/json", "X-Request-ID": f"a12-422-th-{i}"},
                )
                assert response.status_code == 422

        alert_logs = [r for r in caplog.records if r.getMessage() == "Alert condition detected"]
        assert alert_logs
        record = alert_logs[-1]
        assert getattr(record, "status_code", None) == 422
        assert getattr(record, "severity", None) == "warning"
        assert getattr(record, "window_count", 0) >= 5

    def test_alert_log_for_503(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()
        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: False)
        monkeypatch.setattr(api_main.betting_service, "availability_error", lambda: "betting backend unavailable")

        with caplog.at_level(logging.INFO, logger="nba.api.main"):
            first_response = client.get("/api/v1/bets/stats", headers={"X-Request-ID": "a9-503-1"})
            second_response = client.get("/api/v1/bets/stats", headers={"X-Request-ID": "a9-503-2"})

        assert first_response.status_code == 503
        assert second_response.status_code == 503

        observed_logs = [r for r in caplog.records if r.getMessage() == "Alert condition observed (below threshold)"]
        assert observed_logs

        alert_logs = [r for r in caplog.records if r.getMessage() == "Alert condition detected"]
        assert alert_logs
        record = alert_logs[-1]
        assert getattr(record, "request_id", None) == "a9-503-2"
        assert getattr(record, "status_code", None) == 503
        assert getattr(record, "severity", None) == "warning"
        assert getattr(record, "threshold", None) == 2

    def test_alert_log_for_500(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()
        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("predictions service unavailable")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)

        with caplog.at_level(logging.WARNING, logger="nba.api.main"):
            response = client.get("/api/v1/predictions", headers={"X-Request-ID": "a9-500"})

        assert response.status_code == 500
        alert_logs = [r for r in caplog.records if r.getMessage() == "Alert condition detected"]
        assert alert_logs
        record = alert_logs[-1]
        assert getattr(record, "request_id", None) == "a9-500"
        assert getattr(record, "status_code", None) == 500
        assert getattr(record, "severity", None) == "error"
        assert getattr(record, "path", None) == "/api/v1/predictions"
        assert isinstance(getattr(record, "duration_ms", None), float)


class TestIncidentDrill:
    def test_incident_drill_correlation_with_request_id(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()
        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("incident drill predictions error")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        request_id = "drill-incident-001"

        with caplog.at_level(logging.WARNING, logger="nba.api.main"):
            response = client.get("/api/v1/predictions", headers={"X-Request-ID": request_id})

        assert response.status_code == 500
        assert response.headers.get("X-Request-ID") == request_id

        alert_logs = [r for r in caplog.records if r.getMessage() == "Alert condition detected"]
        assert alert_logs
        assert any(getattr(r, "request_id", None) == request_id for r in alert_logs)
        correlated = [r for r in alert_logs if getattr(r, "request_id", None) == request_id]
        assert correlated
        assert all(getattr(r, "status_code", None) == 500 for r in correlated)
