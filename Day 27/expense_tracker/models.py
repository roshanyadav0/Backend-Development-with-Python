"""Data model for a single expense entry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as Date


@dataclass(order=True)
class Expense:
    """A single tracked expense with id, name, amount, category, and date."""

    # sort_index drives .sort() / sorted() — not stored or shown in repr
    sort_index: Date = field(init=False, repr=False, compare=True)

    id: int
    name: str
    amount: float
    category: str
    date: Date
    note: str | None = None

    def __post_init__(self) -> None:
        """Initialise the sort key from the expense date."""
        self.sort_index = self.date

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-safe dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "category": self.category,
            "date": self.date.isoformat(),
            "note": self.note,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> "Expense":
        """Deserialise from a dictionary loaded from JSON."""
        return Expense(
            id=int(data["id"]),  # type: ignore[call-overload]
            name=str(data["name"]),
            amount=float(data["amount"]),  # type: ignore[arg-type]
            category=str(data["category"]),
            date=Date.fromisoformat(str(data["date"])),
            note=str(data["note"]) if data.get("note") else None,
        )

    # ── Display helpers ────────────────────────────────────────────────────

    def amount_str(self) -> str:
        """Return amount formatted as a rupee string."""
        return f"Rs.{self.amount:,.2f}"

    def short(self) -> str:
        """Return a compact one-line summary of the expense."""
        return f"#{self.id} '{self.name}' {self.amount_str()} [{self.category}]"
