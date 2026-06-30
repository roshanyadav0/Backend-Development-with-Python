from __future__ import annotations
from datetime import date
from .models import Expense


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
        return next((e for e in self.expenses if e.id == expense_id), None)

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
