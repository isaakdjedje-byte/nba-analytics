"""Routine SLO/SLA compliance checks for A11."""

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import nba.api.main as api_main


client = TestClient(api_main.app)


class TestRoutineSLOWindow:
    def test_routine_window_error_rates_within_slo(self, monkeypatch: pytest.MonkeyPatch):
        # Synthetic routine window: majority healthy traffic, sparse controlled errors.
        total = 0
        counts = {422: 0, 503: 0, 500: 0}

        for i in range(117):
            response = client.get("/health", headers={"X-Request-ID": f"a11-h-{i}"})
            assert response.status_code == 200
            total += 1

        for i in range(2):
            response = client.post(
                "/api/v1/export",
                data="not json",
                headers={"Content-Type": "application/json", "X-Request-ID": f"a11-422-{i}"},
            )
            assert response.status_code == 422
            counts[422] += 1
            total += 1

        monkeypatch.setattr(api_main.betting_service, "is_available", lambda: False)
        monkeypatch.setattr(api_main.betting_service, "availability_error", lambda: "betting backend unavailable")
        response_503 = client.get("/api/v1/bets/stats", headers={"X-Request-ID": "a11-503-0"})
        assert response_503.status_code == 503
        counts[503] += 1
        total += 1

        def _raise_error(**_: object) -> dict[str, object]:
            raise RuntimeError("a11 synthetic predictions failure")

        monkeypatch.setattr(api_main.predictions_service, "get_predictions_response", _raise_error)
        response_500 = client.get("/api/v1/predictions", headers={"X-Request-ID": "a11-500-0"})
        assert response_500.status_code == 500
        counts[500] += 1
        total += 1

        rate_422 = counts[422] / total
        rate_503 = counts[503] / total
        rate_500 = counts[500] / total

        assert rate_422 <= 0.10  # A10 SLO
        assert rate_503 <= 0.03  # A10 SLO
        assert rate_500 <= 0.01  # A10 SLO
