"""Long-run reliability checks for A13 (SLO trend + signal quality)."""

import logging
from pathlib import Path
import sys
import time

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import nba.api.main as api_main


client = TestClient(api_main.app)


def _window_rates(total: int, c422: int, c503: int, c500: int) -> dict[str, float]:
    return {
        "422": c422 / total,
        "503": c503 / total,
        "500": c500 / total,
    }


class TestLongRunReliability:
    def test_slo_trend_is_stable_across_routine_windows(self, monkeypatch: pytest.MonkeyPatch):
        windows: list[dict[str, float]] = []

        for window_idx in range(3):
            api_main._alert_events.clear()
            total = 0
            c422 = 0
            c503 = 0
            c500 = 0

            for i in range(120):
                response = client.get("/health", headers={"X-Request-ID": f"a13-h-{window_idx}-{i}"})
                assert response.status_code == 200
                total += 1

            for i in range(2):
                response = client.post(
                    "/api/v1/export",
                    data="not json",
                    headers={"Content-Type": "application/json", "X-Request-ID": f"a13-422-{window_idx}-{i}"},
                )
                assert response.status_code == 422
                total += 1
                c422 += 1

            if window_idx != 1:
                monkeypatch.setattr(api_main.betting_service, "is_available", lambda: False)
                monkeypatch.setattr(api_main.betting_service, "availability_error", lambda: "betting backend unavailable")
                response_503 = client.get("/api/v1/bets/stats", headers={"X-Request-ID": f"a13-503-{window_idx}"})
                assert response_503.status_code == 503
                total += 1
                c503 += 1

            if window_idx == 2:
                def _raise_error(**_: object) -> dict[str, object]:
                    raise RuntimeError("a13 synthetic predictions failure")

                monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
                response_500 = client.get("/api/v1/predictions", headers={"X-Request-ID": f"a13-500-{window_idx}"})
                assert response_500.status_code == 500
                total += 1
                c500 += 1

            rates = _window_rates(total, c422, c503, c500)
            windows.append(rates)

            assert rates["422"] <= 0.10
            assert rates["503"] <= 0.03
            assert rates["500"] <= 0.01

        max_500 = max(window["500"] for window in windows)
        min_500 = min(window["500"] for window in windows)
        assert (max_500 - min_500) <= 0.01

    def test_signal_quality_noise_vs_criticality(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()

        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("a13 critical failure")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)

        with caplog.at_level(logging.INFO, logger="nba.api.main"):
            # 422 once: should stay below threshold and avoid high-severity alert noise.
            response_422 = client.post(
                "/api/v1/export",
                data="not json",
                headers={"Content-Type": "application/json", "X-Request-ID": "a13-noise-422"},
            )
            # 500 once: critical signal should alert immediately.
            response_500 = client.get("/api/v1/predictions", headers={"X-Request-ID": "a13-critical-500"})

        assert response_422.status_code == 422
        assert response_500.status_code == 500

        detected = [r for r in caplog.records if r.getMessage() == "Alert condition detected"]
        below = [r for r in caplog.records if r.getMessage() == "Alert condition observed (below threshold)"]

        assert any(getattr(r, "request_id", None) == "a13-noise-422" for r in below)
        assert any(getattr(r, "request_id", None) == "a13-critical-500" for r in detected)

        critical = [r for r in detected if getattr(r, "request_id", None) == "a13-critical-500"]
        assert critical
        assert all(getattr(r, "severity", None) == "error" for r in critical)

    def test_incident_drill_triage_time_with_request_id(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        api_main._alert_events.clear()

        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("a13 incident drill")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        request_id = "a13-drill-001"

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
