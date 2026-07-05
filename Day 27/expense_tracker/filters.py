"""Pure filter functions that operate on a list[Expense].

Each function accepts a list and returns a filtered list.
No file I/O or side effects — easy to unit-test in isolation.
"""

from __future__ import annotations

from .exceptions import NoExpensesError
from .models import Expense
from . import validators


def by_category(expenses: list[Expense], category: str) -> list[Expense]:
    """Return expenses matching *category* (case-insensitive).

    Raises:
        InvalidCategoryError: if category is blank or too long.
        NoExpensesError:      if no expenses match.
    """
    validated = validators.category(category)
    result = [e for e in expenses if e.category.lower() == validated.lower()]
    if not result:
        raise NoExpensesError(f"in category '{validated}'")
    return result


def by_date_range(
    expenses: list[Expense],
    start: str | None = None,
    end: str | None = None,
) -> list[Expense]:
    """Return expenses within [start, end] (both ends inclusive, both optional).

    Raises:
        InvalidDateError:      if either date string is malformed.
        InvalidDateRangeError: if start > end.
        NoExpensesError:       if no expenses fall in the range.
    """
    start_date, end_date = validators.date_range(start, end)

    result = [
        e
        for e in expenses
        if (start_date is None or e.date >= start_date)
        and (end_date is None or e.date <= end_date)
    ]
    if not result:
        label = _range_label(start, end)
        raise NoExpensesError(f"in date range {label}")
    return result


def by_category_and_date(
    expenses: list[Expense],
    category: str,
    start: str | None = None,
    end: str | None = None,
) -> list[Expense]:
    """Apply category filter first, then date range on the result."""
    return by_date_range(by_category(expenses, category), start, end)


def _range_label(start: str | None, end: str | None) -> str:
    """Build a human-readable label for a date range pair."""
    if start and end:
        return f"[{start} → {end}]"
    if start:
        return f"[from {start}]"
    if end:
        return f"[until {end}]"
    return "[all time]"
