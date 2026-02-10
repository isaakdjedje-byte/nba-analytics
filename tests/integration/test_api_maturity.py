"""Operational maturity checks for A16."""

import logging
from pathlib import Path
import sys
import time

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import nba.api.main as api_main


client = TestClient(api_main.app)


class TestBackendOperationalMaturity:
    def test_trend_422_503_500_on_routine_windows(self, monkeypatch: pytest.MonkeyPatch):
        windows = []
        for w in range(4):
            api_main._alert_events.clear()
            total = 0
            c422 = 0
            c503 = 0
            c500 = 0

            for i in range(100):
                response = client.get("/health", headers={"X-Request-ID": f"a16-h-{w}-{i}"})
                assert response.status_code == 200
                total += 1

            for i in range(2):
                response = client.post(
                    "/api/v1/export",
                    data="not json",
                    headers={"Content-Type": "application/json", "X-Request-ID": f"a16-422-{w}-{i}"},
                )
                assert response.status_code == 422
                c422 += 1
                total += 1

            if w % 2 == 0:
                monkeypatch.setattr(api_main.betting_service, "is_available", lambda: False)
                monkeypatch.setattr(api_main.betting_service, "availability_error", lambda: "betting backend unavailable")
                response_503 = client.get("/api/v1/bets/stats", headers={"X-Request-ID": f"a16-503-{w}"})
                assert response_503.status_code == 503
                c503 += 1
                total += 1

            if w == 3:
                def _raise_error(**_: object) -> dict[str, object]:
                    raise RuntimeError("a16 synthetic failure")

                monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
                response_500 = client.get("/api/v1/predictions", headers={"X-Request-ID": f"a16-500-{w}"})
                assert response_500.status_code == 500
                c500 += 1
                total += 1

            rates = {"422": c422 / total, "503": c503 / total, "500": c500 / total}
            windows.append(rates)

            assert rates["422"] <= 0.10
            assert rates["503"] <= 0.03
            assert rates["500"] <= 0.01

        assert max(r["500"] for r in windows) - min(r["500"] for r in windows) <= 0.01

    def test_signal_quality_noise_vs_critical(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()

        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("a16 critical")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        with caplog.at_level(logging.INFO, logger="nba.api.main"):
            response_422 = client.post(
                "/api/v1/export",
                data="not json",
                headers={"Content-Type": "application/json", "X-Request-ID": "a16-noise-422"},
            )
            response_500 = client.get("/api/v1/predictions", headers={"X-Request-ID": "a16-critical-500"})

        assert response_422.status_code == 422
        assert response_500.status_code == 500

        detected = [r for r in caplog.records if r.getMessage() == "Alert condition detected"]
        below = [r for r in caplog.records if r.getMessage() == "Alert condition observed (below threshold)"]
        assert any(getattr(r, "request_id", None) == "a16-noise-422" for r in below)
        critical = [r for r in detected if getattr(r, "request_id", None) == "a16-critical-500"]
        assert critical
        assert all(getattr(r, "severity", None) == "error" for r in critical)

    def test_incident_drill_x_request_id_and_triage(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()

        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("a16 drill")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        request_id = "a16-drill-001"
        start = time.perf_counter()

        with caplog.at_level(logging.WARNING, logger="nba.api.main"):
            response = client.get("/api/v1/predictions", headers={"X-Request-ID": request_id})

        matched = [
            r
            for r in caplog.records
            if r.getMessage() == "Alert condition detected" and getattr(r, "request_id", None) == request_id
        ]
        triage_seconds = time.perf_counter() - start

        assert response.status_code == 500
        assert response.headers.get("X-Request-ID") == request_id
        assert matched
        assert triage_seconds <= 5.0
