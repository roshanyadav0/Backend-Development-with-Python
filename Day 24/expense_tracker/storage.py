from __future__ import annotations
import json
from pathlib import Path
from .models import Expense

DATA_FILE = Path("expenses.json")


def load() -> list[Expense]:
    if not DATA_FILE.exists():
        return []
    raw: list[dict[str, object]] = json.loads(DATA_FILE.read_text())
    return [Expense.from_dict(item) for item in raw]


def save(expenses: list[Expense]) -> None:
    DATA_FILE.write_text(json.dumps([e.to_dict() for e in expenses], indent=2))
