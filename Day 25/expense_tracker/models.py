from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


@dataclass(order=True)          # enables sorting by field order
class Expense:
    # sort_index is not stored — used only for .sort() / sorted()
    sort_index: date = field(init=False, repr=False, compare=True)

    id:       int
    name:     str
    amount:   float
    category: str
    date:     date
    note:     str | None = None

    def __post_init__(self) -> None:
        self.sort_index = self.date     # sort by date by default

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, object]:
        return {
            "id":       self.id,
            "name":     self.name,
            "amount":   self.amount,
            "category": self.category,
            "date":     self.date.isoformat(),
            "note":     self.note,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> Expense:
        return Expense(
            id=int(data["id"]),  # type: ignore[call-overload]
            name=str(data["name"]),
            amount=float(data["amount"]),               # type: ignore[arg-type]
            category=str(data["category"]),
            date=date.fromisoformat(str(data["date"])),
            note=str(data["note"]) if data.get("note") else None,
        )

    # ── Display helpers ────────────────────────────────────────────────────

    def amount_str(self) -> str:
        return f"Rs.{self.amount:,.2f}"

    def short(self) -> str:
        return f"#{self.id} '{self.name}' {self.amount_str()} [{self.category}]"
