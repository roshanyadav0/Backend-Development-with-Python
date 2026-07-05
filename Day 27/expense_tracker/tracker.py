"""Core ExpenseTracker class — business logic and persistence."""

from __future__ import annotations

from datetime import date
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from .exceptions import ExpenseNotFoundError, NoExpensesError
from .models import Expense
from . import filters, storage, validators

F = TypeVar = Callable[..., Any]  # local alias — avoids importing TypeVar


def _mutates(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: persist to disk automatically after each mutating method."""

    @wraps(method)
    def wrapper(self: "ExpenseTracker", *args: Any, **kwargs: Any) -> Any:
        result = method(self, *args, **kwargs)
        self._persist()  # pylint: disable=protected-access
        return result

    return wrapper


class ExpenseTracker:
    """Manage a collection of Expense objects backed by a JSON file.

    All mutating operations (add, update, delete) persist automatically
    via the ``@_mutates`` decorator — callers never need to call save()
    explicitly.

    Example::

        tracker = ExpenseTracker()
        tracker.add("Coffee", 3.50, "Food")
        print(tracker.total)   # 3.5
        print(len(tracker))    # 1
    """

    def __init__(self, data_file: Path = storage.DATA_FILE) -> None:
        """Load existing expenses from *data_file* (created fresh if absent)."""
        self._file = data_file
        self._expenses: list[Expense] = storage.load(self._file)

    # ── Private helpers ────────────────────────────────────────────────────

    def _persist(self) -> None:
        """Write the current expense list to disk."""
        storage.save(self._expenses, self._file)

    def _next_id(self) -> int:
        """Return the next available integer ID."""
        return max((e.id for e in self._expenses), default=0) + 1

    def _find(self, expense_id: int) -> Expense:
        """Return the matching expense, or raise ExpenseNotFoundError."""
        found = next((e for e in self._expenses if e.id == expense_id), None)
        if found is None:
            raise ExpenseNotFoundError(expense_id)
        return found

    # ── Read-only properties ───────────────────────────────────────────────

    @property
    def count(self) -> int:
        """Number of expenses currently tracked."""
        return len(self._expenses)

    @property
    def total(self) -> float:
        """Sum of all expense amounts, rounded to 2 dp."""
        return round(sum(e.amount for e in self._expenses), 2)

    @property
    def categories(self) -> list[str]:
        """Alphabetically sorted list of unique category names."""
        return sorted({e.category for e in self._expenses})

    @property
    def average(self) -> float:
        """Mean expense amount, or 0.0 when there are no expenses."""
        if not self._expenses:
            return 0.0
        return round(self.total / self.count, 2)

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
        """Create, store, and return a new Expense.

        Args:
            name:         Expense description (1-60 chars).
            amount:       Positive amount in rupees.
            category:     Category label (1-30 chars); auto title-cased.
            expense_date: Date of expense; defaults to today.
            note:         Optional free-text note.

        Raises:
            InvalidNameError:     blank or too-long name.
            InvalidAmountError:   amount <= 0.
            InvalidCategoryError: blank or too-long category.
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
        """Update one or more fields on an existing expense and return it.

        Only the keyword arguments that are not None are applied.

        Raises:
            ExpenseNotFoundError: if *expense_id* does not exist.
            (validators raise on invalid values)
        """
        expense = self._find(expense_id)
        if name is not None:
            expense.name = validators.name(name)
        if amount is not None:
            expense.amount = validators.amount(amount)
        if category is not None:
            expense.category = validators.category(category)
        if note is not None:
            expense.note = note.strip() or None
        return expense

    @_mutates
    def delete(self, expense_id: int) -> Expense:
        """Remove an expense by ID and return the deleted object.

        Raises:
            ExpenseNotFoundError: if *expense_id* does not exist.
        """
        expense = self._find(expense_id)
        self._expenses.remove(expense)
        return expense

    # ── Queries ────────────────────────────────────────────────────────────

    def all(self, sort_by: str = "date") -> list[Expense]:
        """Return all expenses sorted by *sort_by*.

        Valid values: ``"date"`` | ``"amount"`` | ``"id"`` |
        ``"category"`` | ``"name"``.  Unknown values fall back to ``"id"``.
        """
        key_map: dict[str, Callable[[Expense], Any]] = {
            "date": lambda e: e.date,
            "amount": lambda e: e.amount,
            "id": lambda e: e.id,
            "category": lambda e: e.category,
            "name": lambda e: e.name,
        }
        key = key_map.get(sort_by, lambda e: e.id)
        return sorted(self._expenses, key=key)

    def get(self, expense_id: int) -> Expense:
        """Return a single expense by ID.

        Raises:
            ExpenseNotFoundError: if *expense_id* does not exist.
        """
        return self._find(expense_id)

    def filter_by_category(self, category: str) -> list[Expense]:
        """Delegate to :func:`filters.by_category`."""
        return filters.by_category(self._expenses, category)

    def filter_by_date(
        self, start: str | None = None, end: str | None = None
    ) -> list[Expense]:
        """Delegate to :func:`filters.by_date_range`."""
        return filters.by_date_range(self._expenses, start, end)

    def filter_by_category_and_date(
        self, category: str, start: str | None = None, end: str | None = None
    ) -> list[Expense]:
        """Delegate to :func:`filters.by_category_and_date`."""
        return filters.by_category_and_date(self._expenses, category, start, end)

    # ── Aggregates ─────────────────────────────────────────────────────────

    def total_by_category(self) -> dict[str, float]:
        """Return a category → total mapping sorted by total descending."""
        totals: dict[str, float] = {}
        for expense in self._expenses:
            totals[expense.category] = round(
                totals.get(expense.category, 0) + expense.amount, 2
            )
        return dict(sorted(totals.items(), key=lambda item: -item[1]))

    def most_expensive(self) -> Expense:
        """Return the highest-amount expense.

        Raises:
            NoExpensesError: if there are no expenses.
        """
        if not self._expenses:
            raise NoExpensesError()
        return max(self._expenses, key=lambda e: e.amount)

    def least_expensive(self) -> Expense:
        """Return the lowest-amount expense.

        Raises:
            NoExpensesError: if there are no expenses.
        """
        if not self._expenses:
            raise NoExpensesError()
        return min(self._expenses, key=lambda e: e.amount)

    # ── Dunder methods ─────────────────────────────────────────────────────

    def __len__(self) -> int:
        """Support ``len(tracker)``."""
        return self.count

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"ExpenseTracker(expenses={self.count}, "
            f"total={self.total:.2f}, file='{self._file}')"
        )

    def __contains__(self, expense_id: int) -> bool:
        """Support ``expense_id in tracker``."""
        return any(e.id == expense_id for e in self._expenses)
