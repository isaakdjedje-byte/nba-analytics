"""API REST FastAPI pour NBA Analytics."""

from datetime import datetime
from collections import defaultdict, deque
import logging
from pathlib import Path
import sys
import time
import uuid
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba.api.routers import calendar
from nba.config import settings
from nba.services import analysis_service, betting_service, catalog_service, predictions_service


logger = logging.getLogger(__name__)

_ALERT_WINDOW_SECONDS = 300
_ALERT_THRESHOLDS = {
    422: 5,
    500: 1,
    503: 2,
}
_ALERT_SEVERITY = {
    422: "warning",
    500: "error",
    503: "warning",
}
_alert_events: dict[tuple[int, str], deque[float]] = defaultdict(deque)


def _record_alert_event(status_code: int, path: str, now: float) -> int:
    key = (status_code, path)
    queue = _alert_events[key]
    queue.append(now)
    cutoff = now - _ALERT_WINDOW_SECONDS
    while queue and queue[0] < cutoff:
        queue.popleft()
    return len(queue)


def _alert_threshold_for(status_code: int, path: str) -> int:
    if status_code == 503 and not path.startswith("/api/v1/bets"):
        return 1
    return _ALERT_THRESHOLDS.get(status_code, 1)


class ExportRequest(BaseModel):
    dataset: str
    format: str = "parquet"
    partition_by: Optional[str] = None


class DatasetInfo(BaseModel):
    name: str
    format: str
    record_count: int
    last_updated: Optional[Any] = None


class BetRequest(BaseModel):
    date: str
    match: str
    prediction: str
    stake: float
    odds: float


class BetResultUpdate(BaseModel):
    bet_id: str
    result: str


app = FastAPI(
    title="NBA Analytics API",
    description="API professionnelle pour données NBA",
    version=settings.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calendar.router, prefix="/api/v1")


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    alert_statuses = {422, 500, 503}
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "Unhandled request error",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
            },
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    if response.status_code in alert_statuses:
        now = time.time()
        window_count = _record_alert_event(response.status_code, request.url.path, now)
        threshold = _alert_threshold_for(response.status_code, request.url.path)
        if window_count >= threshold:
            severity = _ALERT_SEVERITY.get(response.status_code, "warning")
            extra = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "window_count": window_count,
                "window_seconds": _ALERT_WINDOW_SECONDS,
                "threshold": threshold,
                "severity": severity,
            }
            if severity == "error":
                logger.error("Alert condition detected", extra=extra)
            elif severity == "warning":
                logger.warning("Alert condition detected", extra=extra)
            else:
                logger.info("Alert condition detected", extra=extra)
        else:
            logger.info(
                "Alert condition observed (below threshold)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "window_count": window_count,
                    "window_seconds": _ALERT_WINDOW_SECONDS,
                    "threshold": threshold,
                },
            )
    response.headers["X-Request-ID"] = request_id
    return response


@app.on_event("startup")
async def startup_event() -> None:
    if betting_service.is_available():
        try:
            betting_service.initialize_db()
        except Exception:
            logger.exception("Betting backend initialization failed during startup")
    else:
        logger.warning("Betting backend unavailable at startup")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "NBA Analytics API", "version": settings.version}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.version,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/datasets", response_model=list[DatasetInfo])
def list_datasets() -> list[Any]:
    return catalog_service.list_datasets()


@app.get("/api/v1/datasets/{dataset_name}")
def get_dataset_info(dataset_name: str) -> Any:
    info = catalog_service.get_dataset_info(dataset_name)
    if not info:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return info


@app.post("/api/v1/export")
def export_data(request: ExportRequest) -> dict[str, Any]:
    try:
        return catalog_service.export_dataset(
            dataset=request.dataset,
            fmt=request.format,
            partition_by=request.partition_by,
        )
    except FileNotFoundError:
        logger.info("Export failed: dataset not found (%s)", request.dataset)
        raise HTTPException(status_code=404, detail="Dataset not found")
    except ValueError as exc:
        logger.info("Export validation error for dataset %s: %s", request.dataset, exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected export error for dataset %s", request.dataset)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/v1/catalog/scan")
def scan_catalog() -> dict[str, Any]:
    return catalog_service.scan_catalog()


@app.get("/api/v1/predictions")
def get_predictions(
    view: str = "day",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_confidence: float = 0.0,
    team: Optional[str] = None,
) -> dict[str, Any]:
    try:
        return predictions_service.get_predictions_response(
            view=view,
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_confidence,
            team=team,
        )
    except Exception as exc:
        logger.exception("Predictions endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc))


def _require_betting_available() -> None:
    if not betting_service.is_available():
        detail = betting_service.availability_error() or "Betting backend unavailable"
        logger.warning("Betting backend unavailable: %s", detail)
        raise HTTPException(status_code=503, detail=detail)


@app.post("/api/v1/bets")
def create_bet(bet: BetRequest) -> dict[str, Any]:
    _require_betting_available()
    try:
        bet_id = betting_service.place_bet(
            betting_service.BetPayload(
                date=bet.date,
                match=bet.match,
                prediction=bet.prediction,
                stake=bet.stake,
                odds=bet.odds,
            )
        )
    except ValueError as exc:
        logger.info("Bet creation validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    return {"success": True, "bet_id": bet_id}


@app.post("/api/v1/bets/update")
def update_bet(update: BetResultUpdate) -> dict[str, Any]:
    _require_betting_available()
    try:
        profit = betting_service.update_bet_result(update.bet_id, update.result)
        return {"success": True, "profit": profit}
    except ValueError as exc:
        logger.info("Bet update failed for %s: %s", update.bet_id, exc)
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/v1/bets")
def list_bets(status: str = "all", limit: int = 50) -> dict[str, list[dict[str, Any]]]:
    _require_betting_available()
    bets = betting_service.get_bets(status, limit)
    return {
        "bets": [
            {
                "id": bet.id,
                "date": bet.date,
                "match": bet.match,
                "prediction": bet.prediction,
                "stake": bet.stake,
                "odds": bet.odds,
                "result": bet.result,
                "profit": bet.profit,
            }
            for bet in bets
        ]
    }


@app.get("/api/v1/bets/stats")
def betting_stats() -> dict[str, Any]:
    _require_betting_available()
    return betting_service.get_stats()


@app.get("/api/v1/analysis/temporal")
def temporal_analysis() -> dict[str, Any]:
    return analysis_service.temporal_analysis()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
