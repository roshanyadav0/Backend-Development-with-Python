from __future__ import annotations
from datetime import date
from .models import Expense
from .exceptions import (
    ExpenseNotFoundError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
)
from . import filters, storage


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
        """
        Add a new expense.

        Raises:
            InvalidAmountError:   if amount <= 0
            InvalidCategoryError: if category is blank / too long
        """
        if amount <= 0:
            raise InvalidAmountError(amount)

        validated_category = filters.validate_category(category)

        expense = Expense(
            id=self._next_id(),
            name=name.strip(),
            amount=amount,
            category=validated_category,
            date=expense_date or date.today(),
            note=note.strip() if note else None,
        )
        self.expenses.append(expense)
        self._save()
        return expense

    # ── View ───────────────────────────────────────────────────────────────

    def all(self) -> list[Expense]:
        return list(self.expenses)

    def get(self, expense_id: int) -> Expense:
        """
        Raises:
            ExpenseNotFoundError: if ID doesn't exist
        """
        found = next((e for e in self.expenses if e.id == expense_id), None)
        if found is None:
            raise ExpenseNotFoundError(expense_id)
        return found

    # ── Filters ────────────────────────────────────────────────────────────

    def filter_by_category(self, category: str) -> list[Expense]:
        return filters.by_category(self.expenses, category)

    def filter_by_date(
        self,
        start: str | None = None,
        end: str | None = None,
    ) -> list[Expense]:
        return filters.by_date_range(self.expenses, start, end)

    def filter_by_category_and_date(
        self,
        category: str,
        start: str | None = None,
        end: str | None = None,
    ) -> list[Expense]:
        return filters.by_category_and_date(self.expenses, category, start, end)

    # ── Delete ─────────────────────────────────────────────────────────────

    def delete(self, expense_id: int) -> Expense:
        """
        Raises:
            ExpenseNotFoundError: if ID doesn't exist
        """
        expense = self.get(expense_id)   # raises if not found
        self.expenses.remove(expense)
        self._save()
        return expense

    # ── Summary ────────────────────────────────────────────────────────────

    def total(self) -> float:
        return sum(e.amount for e in self.expenses)

    def by_category(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for e in self.expenses:
            totals[e.category] = totals.get(e.category, 0) + e.amount
        return totals
