from __future__ import annotations
from datetime import date
from pathlib import Path
from functools import wraps
from typing import Callable, TypeVar, Any
from .models import Expense
from .exceptions import ExpenseNotFoundError, NoExpensesError
from . import validators, filters, storage

F = TypeVar("F", bound=Callable[..., Any])


# ── Class decorator: auto-save after every mutating method ────────────────────

def _mutates(method: F) -> F:
    """Save to disk automatically after the decorated method runs."""
    @wraps(method)
    def wrapper(self: "ExpenseTracker", *args: Any, **kwargs: Any) -> Any:
        result = method(self, *args, **kwargs)
        self._save()
        return result
    return wrapper  # type: ignore[return-value]


# ── ExpenseTracker ─────────────────────────────────────────────────────────────

class ExpenseTracker:
    """
    Full OOP expense tracker.

    Responsibilities:
      - Validate input (via validators module)
      - Manage the in-memory list[Expense]
      - Persist to JSON on every mutation (via @_mutates)
      - Delegate filtering to filters module
      - Never touch display / CLI concerns
    """

    def __init__(self, data_file: Path = storage.DATA_FILE) -> None:
        self._file = data_file
        self._expenses: list[Expense] = storage.load(self._file)

    # ── Internal helpers ───────────────────────────────────────────────────

    def _save(self) -> None:
        storage.save(self._expenses, self._file)

    def _next_id(self) -> int:
        return max((e.id for e in self._expenses), default=0) + 1

    def _find(self, expense_id: int) -> Expense:
        """Return the expense or raise ExpenseNotFoundError."""
        found = next((e for e in self._expenses if e.id == expense_id), None)
        if found is None:
            raise ExpenseNotFoundError(expense_id)
        return found

    # ── Properties (read-only views) ───────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self._expenses)

    @property
    def total(self) -> float:
        return round(sum(e.amount for e in self._expenses), 2)

    @property
    def categories(self) -> list[str]:
        """Sorted unique category list."""
        return sorted({e.category for e in self._expenses})

    # ── CRUD ───────────────────────────────────────────────────────────────

    @_mutates
    def add(
        self,
        name: str,
        amount: float,
        category: str,
        expense_date: date | None = None,
        note: str | None = None,
    ) -> Expense:
        """
        Add and persist a new expense.

        Raises:
            InvalidNameError:     blank / too long name
            InvalidAmountError:   amount <= 0
            InvalidCategoryError: blank / too long category
        """
        expense = Expense(
            id=self._next_id(),
            name=validators.name(name),
            amount=validators.amount(amount),
            category=validators.category(category),
            date=expense_date or date.today(),
            note=note.strip() if note else None,
        )
        self._expenses.append(expense)
        return expense

    @_mutates
    def update(
        self,
        expense_id: int,
        name: str | None = None,
        amount: float | None = None,
        category: str | None = None,
        note: str | None = None,
    ) -> Expense:
        """
        Update one or more fields on an existing expense.

        Raises:
            ExpenseNotFoundError: if ID doesn't exist
            (validators raise on bad values)
        """
        expense = self._find(expense_id)
        if name     is not None: expense.name     = validators.name(name)
        if amount   is not None: expense.amount   = validators.amount(amount)
        if category is not None: expense.category = validators.category(category)
        if note     is not None: expense.note     = note.strip() or None
        return expense

    @_mutates
    def delete(self, expense_id: int) -> Expense:
        """
        Delete an expense and return it.

        Raises:
            ExpenseNotFoundError: if ID doesn't exist
        """
        expense = self._find(expense_id)
        self._expenses.remove(expense)
        return expense

    # ── Queries ────────────────────────────────────────────────────────────

    def all(self, sort_by: str = "date") -> list[Expense]:
        """
        Return all expenses sorted by field.

        sort_by options: "date" | "amount" | "id" | "category" | "name"
        Unknown sort_by silently falls back to "id".
        """
        key_map: dict[str, Callable[[Expense], Any]] = {
            "date":     lambda e: e.date,
            "amount":   lambda e: e.amount,
            "id":       lambda e: e.id,
            "category": lambda e: e.category,
            "name":     lambda e: e.name,
        }
        key = key_map.get(sort_by, lambda e: e.id)
        return sorted(self._expenses, key=key)

    def get(self, expense_id: int) -> Expense:
        """
        Raises:
            ExpenseNotFoundError: if ID doesn't exist
        """
        return self._find(expense_id)

    def filter_by_category(self, category: str) -> list[Expense]:
        return filters.by_category(self._expenses, category)

    def filter_by_date(
        self, start: str | None = None, end: str | None = None
    ) -> list[Expense]:
        return filters.by_date_range(self._expenses, start, end)

    def filter_by_category_and_date(
        self, category: str, start: str | None = None, end: str | None = None
    ) -> list[Expense]:
        return filters.by_category_and_date(self._expenses, category, start, end)

    # ── Aggregates ─────────────────────────────────────────────────────────

    def total_by_category(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for e in self._expenses:
            totals[e.category] = round(totals.get(e.category, 0) + e.amount, 2)
        return dict(sorted(totals.items(), key=lambda x: -x[1]))

    def most_expensive(self) -> Expense:
        """
        Raises:
            NoExpensesError: if no expenses exist
        """
        if not self._expenses:
            raise NoExpensesError()
        return max(self._expenses, key=lambda e: e.amount)

    def least_expensive(self) -> Expense:
        """
        Raises:
            NoExpensesError: if no expenses exist
        """
        if not self._expenses:
            raise NoExpensesError()
        return min(self._expenses, key=lambda e: e.amount)

    @property
    def average(self) -> float:
        if not self._expenses:
            return 0.0
        return round(self.total / self.count, 2)

    # ── Dunder methods ─────────────────────────────────────────────────────

    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return (
            f"ExpenseTracker(expenses={self.count}, "
            f"total={self.total:.2f}, file='{self._file}')"
        )

    def __contains__(self, expense_id: int) -> bool:
        """Supports: `if 3 in tracker`"""
        return any(e.id == expense_id for e in self._expenses)
