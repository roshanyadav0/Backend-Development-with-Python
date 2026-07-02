from __future__ import annotations
from dataclasses import dataclass
from datetime import date


@dataclass
class Expense:
    id: int
    name: str
    amount: float
    category: str
    date: date
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "category": self.category,
            "date": self.date.isoformat(),
            "note": self.note,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> Expense:
        return Expense(
            id=int(data["id"]),             # type: ignore[call-overload]
            name=str(data["name"]),
            amount=float(data["amount"]),   # type: ignore[arg-type]
            category=str(data["category"]),
            date=date.fromisoformat(str(data["date"])),
            note=str(data["note"]) if data.get("note") else None,
        )
