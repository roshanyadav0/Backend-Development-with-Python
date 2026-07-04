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
    """Validate amount > 0."""
    if value <= 0:
        raise InvalidAmountError(value)
    return round(value, 2)


def name(value: str) -> str:
    """Validate and normalise expense name."""
    stripped = value.strip()
    if not stripped or len(stripped) > 60:
        raise InvalidNameError(value)
    return stripped


def category(value: str) -> str:
    """Validate and title-case category."""
    stripped = value.strip()
    if not stripped or len(stripped) > 30:
        raise InvalidCategoryError(value)
    return stripped.title()          # "food" → "Food"


def parse_date(value: str) -> date:
    """Parse YYYY-MM-DD or raise InvalidDateError."""
    stripped = value.strip()
    if not stripped:
        raise InvalidDateError(value)
    try:
        parsed = date.fromisoformat(stripped)
        # Reject anything that isn't exactly YYYY-MM-DD (10 chars)
        if len(stripped) != 10 or stripped[4] != "-" or stripped[7] != "-":
            raise InvalidDateError(value)
        return parsed
    except ValueError:
        raise InvalidDateError(value)


def date_range(
    start: str | None,
    end: str | None,
) -> tuple[date | None, date | None]:
    """
    Parse and validate a date range pair.
    Returns (start_date, end_date) — either may be None.

    Raises:
        InvalidDateError:      if either string is malformed
        InvalidDateRangeError: if start > end
    """
    start_date = parse_date(start) if start else None
    end_date   = parse_date(end)   if end   else None

    if start_date and end_date and start_date > end_date:
        raise InvalidDateRangeError(start, end)   # type: ignore[arg-type]

    return start_date, end_date
