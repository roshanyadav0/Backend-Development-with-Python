from __future__ import annotations
from dataclasses import dataclass
from datetime import date


@dataclass
class Expense:
    id: int
    title: str
    amount: float
    category: str
    date: date
    note: str | None = None
