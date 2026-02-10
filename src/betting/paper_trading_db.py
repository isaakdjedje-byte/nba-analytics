"""
SQLite database for paper trading.
Single source of truth for all paper trading data.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

DB_PATH = Path("data/paper_trading.db")


@dataclass
class Bet:
    id: str
    date: str
    match: str
    prediction: str
    stake: float
    odds: float
    result: Optional[str] = None
    profit: Optional[float] = None
    created_at: Optional[str] = None


def init_db():
    """Initialize SQLite database with schema."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            match TEXT NOT NULL,
            prediction TEXT NOT NULL,
            stake REAL NOT NULL,
            odds REAL NOT NULL,
            result TEXT DEFAULT 'pending',
            profit REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Index for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bets_date ON bets(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bets_result ON bets(result)")
    
    # Materialized view for stats
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS paper_trading_stats AS 
        SELECT 
            COUNT(*) as total_bets,
            SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as won_bets,
            SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as lost_bets,
            SUM(CASE WHEN result = 'pending' THEN 1 ELSE 0 END) as pending_bets,
            SUM(COALESCE(profit, 0)) as total_profit,
            AVG(CASE WHEN result != 'pending' THEN profit END) as avg_profit,
            ROUND(
                CAST(SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS FLOAT) / 
                NULLIF(SUM(CASE WHEN result != 'pending' THEN 1 ELSE 0 END), 0) * 100, 
                2
            ) as win_rate
        FROM bets
    """)
    
    conn.commit()
    conn.close()


def place_bet(bet: Bet) -> str:
    """Place a new paper trading bet."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    bet_id = f"bet_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:8]}"
    
    cursor.execute("""
        INSERT INTO bets (id, date, match, prediction, stake, odds)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (bet_id, bet.date, bet.match, bet.prediction, bet.stake, bet.odds))
    
    conn.commit()
    conn.close()
    return bet_id


def update_bet_result(bet_id: str, result: str) -> float:
    """Update bet result and calculate profit."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get bet details
    cursor.execute("SELECT stake, odds FROM bets WHERE id = ?", (bet_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Bet {bet_id} not found")
    
    stake, odds = row
    
    # Calculate profit
    if result == 'win':
        profit = stake * (odds - 1)
    else:
        profit = -stake
    
    cursor.execute("""
        UPDATE bets 
        SET result = ?, profit = ? 
        WHERE id = ?
    """, (result, profit, bet_id))
    
    conn.commit()
    conn.close()
    return profit


def get_bets(status: str = "all", limit: int = 50) -> List[Bet]:
    """Get bets with optional filter."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if status == "all":
        cursor.execute("""
            SELECT id, date, match, prediction, stake, odds, result, profit, created_at
            FROM bets 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT id, date, match, prediction, stake, odds, result, profit, created_at
            FROM bets 
            WHERE result = ?
            ORDER BY created_at DESC 
            LIMIT ?
        """, (status, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [Bet(*row) for row in rows]


def get_stats() -> Dict:
    """Get paper trading statistics from view."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM paper_trading_stats")
    row = cursor.fetchone()
    
    # Valeurs par défaut à 0
    default_stats = {
        "total_bets": 0,
        "won_bets": 0,
        "lost_bets": 0,
        "pending_bets": 0,
        "total_profit": 0.0,
        "avg_profit": 0.0,
        "win_rate": 0.0
    }
    
    if not row:
        conn.close()
        return default_stats
    
    columns = [description[0] for description in cursor.description]
    stats = dict(zip(columns, row))
    
    # Remplacer None par 0
    for key in stats:
        if stats[key] is None:
            stats[key] = 0 if key not in ['total_profit', 'avg_profit'] else 0.0
    
    # S'assurer que toutes les clés existent
    for key, value in default_stats.items():
        if key not in stats or stats[key] is None:
            stats[key] = value
    
    conn.close()
    return stats
