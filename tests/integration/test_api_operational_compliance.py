"""Operational compliance checks for A15."""

import logging
from pathlib import Path
import sys
import time

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import nba.api.main as api_main


client = TestClient(api_main.app)


class TestOperationalComplianceA15:
    def test_slo_sla_422_503_500_window(self, monkeypatch: pytest.MonkeyPatch):
        api_main._alert_events.clear()

        total = 0
        c422 = 0
        c503 = 0
        c500 = 0

        for i in range(120):
            response = client.get("/health", headers={"X-Request-ID": f"a15-h-{i}"})
            assert response.status_code == 200
            total += 1

        for i in range(2):
            response = client.post(
                "/api/v1/export",
                data="not json",
                headers={"Content-Type": "application/json", "X-Request-ID": f"a15-422-{i}"},
            )
            assert response.status_code == 422
            c422 += 1
            total += 1

        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: False)
        monkeypatch.setattr(api_main.betting_service, "availability_error", lambda: "betting backend unavailable")
        response_503 = client.get("/api/v1/bets/stats", headers={"X-Request-ID": "a15-503-0"})
        assert response_503.status_code == 503
        c503 += 1
        total += 1

        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("a15 synthetic predictions failure")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        response_500 = client.get("/api/v1/predictions", headers={"X-Request-ID": "a15-500-0"})
        assert response_500.status_code == 500
        c500 += 1
        total += 1

        assert (c422 / total) <= 0.10
        assert (c503 / total) <= 0.03
        assert (c500 / total) <= 0.01

    def test_signal_quality_noise_vs_criticality(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()

        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("a15 critical predictions failure")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)

        with caplog.at_level(logging.INFO, logger="nba.api.main"):
            response_422 = client.post(
                "/api/v1/export",
                data="not json",
                headers={"Content-Type": "application/json", "X-Request-ID": "a15-noise-422"},
            )
            response_500 = client.get("/api/v1/predictions", headers={"X-Request-ID": "a15-critical-500"})

        assert response_422.status_code == 422
        assert response_500.status_code == 500

        detected = [r for r in caplog.records if r.getMessage() == "Alert condition detected"]
        below = [r for r in caplog.records if r.getMessage() == "Alert condition observed (below threshold)"]

        assert any(getattr(r, "request_id", None) == "a15-noise-422" for r in below)
        critical = [r for r in detected if getattr(r, "request_id", None) == "a15-critical-500"]
        assert critical
        assert all(getattr(r, "severity", None) == "error" for r in critical)

    def test_runbook_drill_x_request_id_and_triage_time(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()

        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("a15 drill incident")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        request_id = "a15-drill-001"

        start = time.perf_counter()
        with caplog.at_level(logging.WARNING, logger="nba.api.main"):
            response = client.get("/api/v1/predictions", headers={"X-Request-ID": request_id})

        correlated = [
            r
            for r in caplog.records
            if r.getMessage() == "Alert condition detected" and getattr(r, "request_id", None) == request_id
        ]
        triage_seconds = time.perf_counter() - start

        assert response.status_code == 500
        assert response.headers.get("X-Request-ID") == request_id
        assert correlated
        assert triage_seconds <= 5.0
