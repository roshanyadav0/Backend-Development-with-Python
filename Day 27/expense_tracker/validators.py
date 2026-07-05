"""Input validation functions for the Expense Tracker.

Each function validates one field and raises a domain-specific exception
on failure. All functions are pure (no side effects).
"""

from __future__ import annotations

from datetime import date

from .exceptions import (
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
    InvalidDateRangeError,
    InvalidNameError,
)


def amount(value: float) -> float:
    """Return value rounded to 2 dp, or raise InvalidAmountError if <= 0."""
    if value <= 0:
        raise InvalidAmountError(value)
    return round(value, 2)


def name(value: str) -> str:
    """Return stripped name, or raise InvalidNameError if blank/too long."""
    stripped = value.strip()
    if not stripped or len(stripped) > 60:
        raise InvalidNameError(value)
    return stripped


def category(value: str) -> str:
    """Return title-cased category, or raise InvalidCategoryError if invalid."""
    stripped = value.strip()
    if not stripped or len(stripped) > 30:
        raise InvalidCategoryError(value)
    return stripped.title()  # "food" → "Food"


def parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD string, or raise InvalidDateError."""
    stripped = value.strip()
    if not stripped:
        raise InvalidDateError(value)
    # Enforce strict YYYY-MM-DD shape before calling fromisoformat,
    # which accepts partial formats like "2024" in Python 3.11+.
    if len(stripped) != 10 or stripped[4] != "-" or stripped[7] != "-":
        raise InvalidDateError(value)
    try:
        return date.fromisoformat(stripped)
    except ValueError as exc:
        raise InvalidDateError(value) from exc


def date_range(
    start: str | None,
    end: str | None,
) -> tuple[date | None, date | None]:
    """Parse and validate a date range pair; either bound may be None.

    Returns:
        (start_date, end_date) — either may be None (open-ended range).

    Raises:
        InvalidDateError:      if either non-None string is malformed.
        InvalidDateRangeError: if start_date > end_date.
    """
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    if start_date and end_date and start_date > end_date:
        raise InvalidDateRangeError(start, end)  # type: ignore[arg-type]

    return start_date, end_date
