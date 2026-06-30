# 4. Annotate Your Entire Expense Project

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Expense:
    id: int
    title: str
    amount: float
    category: str
    date: date
    note: str | None = None


class ExpenseTracker:
    def __init__(self) -> None:
        self.expenses: list[Expense] = []
        self._next_id: int = 1

    def add_expense(
        self,
        title: str,
        amount: float,
        category: str,
        note: str | None = None,
    ) -> Expense:
        expense = Expense(
            id=self._next_id,
            title=title,
            amount=amount,
            category=category,
            date=date.today(),
            note=note,
        )
        self.expenses.append(expense)
        self._next_id += 1
        return expense

    def get_by_id(self, expense_id: int) -> Expense | None:
        for exp in self.expenses:
            if exp.id == expense_id:
                return exp
        return None

    def delete_expense(self, expense_id: int) -> bool:
        expense = self.get_by_id(expense_id)
        if expense is None:
            return False
        self.expenses.remove(expense)
        return True

    def filter_by_category(self, category: str) -> list[Expense]:
        return [e for e in self.expenses if e.category == category]

    def total_spent(self) -> float:
        return sum(e.amount for e in self.expenses)

    def total_by_category(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for e in self.expenses:
            totals[e.category] = totals.get(e.category, 0) + e.amount
        return totals

    def to_dict_list(self) -> list[dict[str, str | float | int | None]]:
        return [
            {
                "id": e.id,
                "title": e.title,
                "amount": e.amount,
                "category": e.category,
                "note": e.note,
            }
            for e in self.expenses
        ]


def load_expenses_from_dicts(data: list[dict[str, object]]) -> list[Expense]:
    return [
        Expense(
            id=int(d["id"]),                       # type: ignore[arg-type]
            title=str(d["title"]),
            amount=float(d["amount"]),              # type: ignore[arg-type]
            category=str(d["category"]),
            date=date.today(),
            note=d.get("note"),                     # type: ignore[arg-type]
        )
        for d in data
    ]