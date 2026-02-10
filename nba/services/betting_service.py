"""Service wrappers for betting endpoints with lazy imports."""

from dataclasses import dataclass
import logging
from typing import Any, Optional


_IMPORT_ERROR: Optional[Exception] = None
_BETTING_MODULE: Optional[Any] = None
logger = logging.getLogger(__name__)


@dataclass
class BetPayload:
    date: str
    match: str
    prediction: str
    stake: float
    odds: float


def _load_betting_module() -> Any:
    global _BETTING_MODULE, _IMPORT_ERROR
    if _BETTING_MODULE is not None:
        return _BETTING_MODULE
    if _IMPORT_ERROR is not None:
        raise _IMPORT_ERROR

    try:
        from src.betting import paper_trading_db

        _BETTING_MODULE = paper_trading_db
        return _BETTING_MODULE
    except Exception as exc:  # pragma: no cover - defensive import wrapper
        _IMPORT_ERROR = exc
        raise


def is_available() -> bool:
    try:
        _load_betting_module()
        return True
    except Exception:
        return False


def availability_error() -> Optional[str]:
    if _IMPORT_ERROR is None:
        return None
    return str(_IMPORT_ERROR)


def initialize_db() -> None:
    module = _load_betting_module()
    module.init_db()


def place_bet(payload: BetPayload) -> str:
    if payload.stake < 0:
        logger.info("Rejected bet with negative stake: %s", payload.stake)
        raise ValueError("stake must be >= 0")
    if payload.odds < 1:
        logger.info("Rejected bet with invalid odds: %s", payload.odds)
        raise ValueError("odds must be >= 1")

    module = _load_betting_module()
    bet_model = module.Bet(
        id="",
        date=payload.date,
        match=payload.match,
        prediction=payload.prediction,
        stake=payload.stake,
        odds=payload.odds,
    )
    return module.place_bet(bet_model)


def update_bet_result(bet_id: str, result: str) -> float:
    module = _load_betting_module()
    return module.update_bet_result(bet_id, result)


def get_bets(status: str = "all", limit: int = 50) -> list[Any]:
    module = _load_betting_module()
    return module.get_bets(status, limit)


def get_stats() -> dict[str, Any]:
    module = _load_betting_module()
    return module.get_stats()
