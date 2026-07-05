"""Custom exceptions for the Expense Tracker application.

Hierarchy:
    ExpenseTrackerError          ← catch-all base
    ├── ExpenseNotFoundError
    ├── NoExpensesError
    ├── InvalidAmountError
    ├── InvalidDateError
    ├── InvalidDateRangeError
    ├── InvalidCategoryError
    ├── InvalidNameError
    └── StorageError
"""

from __future__ import annotations


class ExpenseTrackerError(Exception):
    """Root exception — catch this to handle any tracker error."""

    exit_code: int = 1


class ExpenseNotFoundError(ExpenseTrackerError):
    """Raised when an expense ID does not exist in the tracker."""

    def __init__(self, expense_id: int) -> None:
        self.expense_id = expense_id
        super().__init__(f"No expense found with ID {expense_id}")


class NoExpensesError(ExpenseTrackerError):
    """Raised when a query returns an empty result set."""

    def __init__(self, context: str = "") -> None:
        super().__init__(f"No expenses found{' ' + context if context else ''}")


class InvalidAmountError(ExpenseTrackerError):
    """Raised when an amount is zero or negative."""

    def __init__(self, amount: float) -> None:
        self.amount = amount
        super().__init__(f"Amount must be > 0, got {amount}")


class InvalidDateError(ExpenseTrackerError):
    """Raised when a date string cannot be parsed as YYYY-MM-DD."""

    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Invalid date '{value}' — use YYYY-MM-DD")


class InvalidDateRangeError(ExpenseTrackerError):
    """Raised when the start date is later than the end date."""

    def __init__(self, start: str, end: str) -> None:
        super().__init__(f"Start date {start} is after end date {end}")


class InvalidCategoryError(ExpenseTrackerError):
    """Raised when a category name is blank or exceeds 30 characters."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(
            f"Invalid category '{category.strip()}' — must be 1-30 non-blank chars"
        )


class InvalidNameError(ExpenseTrackerError):
    """Raised when an expense name is blank or exceeds 60 characters."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(
            f"Invalid name '{name.strip()}' — must be 1-60 non-blank chars"
        )


class StorageError(ExpenseTrackerError):
    """Raised when the JSON data file cannot be read or written."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        super().__init__(f"Storage error ({path}): {reason}")
