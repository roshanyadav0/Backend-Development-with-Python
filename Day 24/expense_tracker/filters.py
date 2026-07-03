from __future__ import annotations
from datetime import date
from .models import Expense
from .exceptions import (
    InvalidDateError,
    InvalidDateRangeError,
    InvalidCategoryError,
    NoExpensesError,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD string or raise InvalidDateError."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise InvalidDateError(value)


def validate_category(category: str) -> str:
    """Strip and validate category, raise InvalidCategoryError if bad."""
    stripped = category.strip()
    if not stripped or len(stripped) > 30:
        raise InvalidCategoryError(category)
    return stripped


# ── Filter functions — each returns list[Expense] ────────────────────────────

def by_category(expenses: list[Expense], category: str) -> list[Expense]:
    """
    Filter expenses by category (case-insensitive).

    Raises:
        InvalidCategoryError: if category is blank / too long
        NoExpensesError: if no expenses match
    """
    validated = validate_category(category)
    result = [
        e for e in expenses
        if e.category.lower() == validated.lower()
    ]
    if not result:
        raise NoExpensesError(f"in category '{validated}'")
    return result


def by_date_range(
    expenses: list[Expense],
    start: str | None = None,
    end: str | None = None,
) -> list[Expense]:
    """
    Filter expenses between start and end dates (inclusive).
    Both are optional — omitting start means "from beginning",
    omitting end means "up to today".

    Raises:
        InvalidDateError: if either date string is malformed
        InvalidDateRangeError: if start > end
        NoExpensesError: if no expenses fall in the range
    """
    start_date: date | None = parse_date(start) if start else None
    end_date: date | None   = parse_date(end)   if end   else None

    if start_date and end_date and start_date > end_date:
        raise InvalidDateRangeError(start, end)  # type: ignore[arg-type]

    result = [
        e for e in expenses
        if (start_date is None or e.date >= start_date)
        and (end_date is None   or e.date <= end_date)
    ]
    if not result:
        range_desc = _range_label(start, end)
        raise NoExpensesError(f"in date range {range_desc}")
    return result


def by_category_and_date(
    expenses: list[Expense],
    category: str,
    start: str | None = None,
    end: str | None = None,
) -> list[Expense]:
    """
    Combine category + date range filters.
    Applies category first, then date range on the result.
    """
    cat_filtered = by_category(expenses, category)
    return by_date_range(cat_filtered, start, end)


# ── Label helper ──────────────────────────────────────────────────────────────

def _range_label(start: str | None, end: str | None) -> str:
    if start and end:
        return f"[{start} → {end}]"
    if start:
        return f"[from {start}]"
    if end:
        return f"[until {end}]"
    return "[all time]"
