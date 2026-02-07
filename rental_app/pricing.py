from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def days_between(start: date, end: date) -> int:
    days = (end - start).days
    return max(1, days)


def year_factor(year: int) -> float:
    age = max(0, date.today().year - year)
    return 1.0 - min(age * 0.01, 0.30)


def period_factor(days: int) -> float:
    if days <= 3:
        return 1.0
    if days <= 7:
        return 0.95
    if days <= 14:
        return 0.90
    return 0.85


def loyalty_factor(conn: sqlite3.Connection, customer_id: int) -> float:
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM rentals
        WHERE customer_id = ?
          AND actual_return_date IS NOT NULL
        """,
        (customer_id,),
    ).fetchone()
    total = row["total"] if row else 0
    if total >= 5:
        return 0.90
    if total >= 3:
        return 0.95
    return 1.0


@dataclass
class CostBreakdown:
    days: int
    base_daily: float
    year_factor: float
    period_factor: float
    loyalty_factor: float
    penalty_rate: float
    subtotal: float
    penalty: float
    total: float


def calculate_cost(
    car: sqlite3.Row,
    days: int,
    loyalty: float,
    return_condition: str | None,
) -> CostBreakdown:
    base_daily = float(car["rental_cost"])
    yf = year_factor(int(car["year"]))
    pf = period_factor(days)
    subtotal = base_daily * days * yf * pf * loyalty
    penalty_rate = 0.20 if return_condition == "poor" else 0.0
    penalty = subtotal * penalty_rate
    total = subtotal + penalty
    return CostBreakdown(
        days=days,
        base_daily=base_daily,
        year_factor=yf,
        period_factor=pf,
        loyalty_factor=loyalty,
        penalty_rate=penalty_rate,
        subtotal=subtotal,
        penalty=penalty,
        total=total,
    )
