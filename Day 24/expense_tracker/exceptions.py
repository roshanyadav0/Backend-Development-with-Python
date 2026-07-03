from __future__ import annotations


# ── Base ──────────────────────────────────────────────────────────────────────

class ExpenseTrackerError(Exception):
    """Root exception — catch this to handle any tracker error."""


# ── Lookup errors ─────────────────────────────────────────────────────────────

class ExpenseNotFoundError(ExpenseTrackerError):
    """Raised when an expense ID does not exist."""

    def __init__(self, expense_id: int) -> None:
        self.expense_id = expense_id
        super().__init__(f"No expense found with ID {expense_id}")


class NoExpensesError(ExpenseTrackerError):
    """Raised when a query returns an empty result set."""

    def __init__(self, context: str = "") -> None:
        msg = "No expenses found"
        if context:
            msg += f" {context}"
        super().__init__(msg)


# ── Validation errors ─────────────────────────────────────────────────────────

class InvalidAmountError(ExpenseTrackerError):
    """Raised when an amount is zero or negative."""

    def __init__(self, amount: float) -> None:
        self.amount = amount
        super().__init__(f"Amount must be greater than 0, got {amount}")


class InvalidDateError(ExpenseTrackerError):
    """Raised when a date string cannot be parsed as YYYY-MM-DD."""

    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Invalid date '{value}'. Expected format: YYYY-MM-DD")


class InvalidDateRangeError(ExpenseTrackerError):
    """Raised when the start date is after the end date."""

    def __init__(self, start: str, end: str) -> None:
        self.start = start
        self.end = end
        super().__init__(f"Start date {start} is after end date {end}")


class InvalidCategoryError(ExpenseTrackerError):
    """Raised when a category name is blank or too long."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(
            f"Invalid category '{category}'. Must be 1-30 non-blank characters."
        )
