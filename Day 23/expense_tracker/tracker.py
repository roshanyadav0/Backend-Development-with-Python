from __future__ import annotations
from datetime import date
from .models import Expense
from . import storage


class ExpenseTracker:
    def __init__(self) -> None:
        self.expenses: list[Expense] = storage.load()

    def _next_id(self) -> int:
        return max((e.id for e in self.expenses), default=0) + 1

    def _save(self) -> None:
        storage.save(self.expenses)

    # ── Add ────────────────────────────────────────────────────────────────
    def add(
        self,
        name: str,
        amount: float,
        category: str,
        expense_date: date | None = None,
        note: str | None = None,
    ) -> Expense:
        expense = Expense(
            id=self._next_id(),
            name=name,
            amount=amount,
            category=category,
            date=expense_date or date.today(),
            note=note,
        )
        self.expenses.append(expense)
        self._save()
        return expense

    # ── View ───────────────────────────────────────────────────────────────
    def all(self) -> list[Expense]:
        return self.expenses

    def get(self, expense_id: int) -> Expense | None:
        return next((e for e in self.expenses if e.id == expense_id), None)

    # ── Delete ─────────────────────────────────────────────────────────────
    def delete(self, expense_id: int) -> bool:
        expense = self.get(expense_id)
        if expense is None:
            return False
        self.expenses.remove(expense)
        self._save()
        return True

    # ── Summary ────────────────────────────────────────────────────────────
    def total(self) -> float:
        return sum(e.amount for e in self.expenses)

    def by_category(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for e in self.expenses:
            totals[e.category] = totals.get(e.category, 0) + e.amount
        return totals
