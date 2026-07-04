from __future__ import annotations
from datetime import date
from .models import Expense
from .exceptions import NoExpensesError
from . import validators


def by_category(expenses: list[Expense], category: str) -> list[Expense]:
    """
    Filter expenses by category (case-insensitive after title-casing).

    Raises:
        InvalidCategoryError: blank / too long category
        NoExpensesError:      no matches
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
    """
    Filter expenses within a date range (both ends inclusive, both optional).

    Raises:
        InvalidDateError:      malformed date string
        InvalidDateRangeError: start > end
        NoExpensesError:       no matches
    """
    start_date, end_date = validators.date_range(start, end)

    result = [
        e for e in expenses
        if (start_date is None or e.date >= start_date)
        and (end_date   is None or e.date <= end_date)
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
    """Category filter first, then date range on the result."""
    return by_date_range(by_category(expenses, category), start, end)


def _range_label(start: str | None, end: str | None) -> str:
    if start and end:
        return f"[{start} → {end}]"
    if start:
        return f"[from {start}]"
    if end:
        return f"[until {end}]"
    return "[all time]"
