from __future__ import annotations
import json
from pathlib import Path
from datetime import date
from .models import Expense


def save_to_file(expenses: list[Expense], path: str | Path) -> None:
    data = [
        {
            "id": e.id,
            "title": e.title,
            "amount": e.amount,
            "category": e.category,
            "date": e.date.isoformat(),
            "note": e.note,
        }
        for e in expenses
    ]
    Path(path).write_text(json.dumps(data, indent=2))


def load_from_file(path: str | Path) -> list[Expense]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    raw = json.loads(file_path.read_text())
    return [
        Expense(
            id=item["id"],
            title=item["title"],
            amount=item["amount"],
            category=item["category"],
            date=date.fromisoformat(item["date"]),
            note=item.get("note"),
        )
        for item in raw
    ]
