from __future__ import annotations


class ExpenseTrackerError(Exception):
    """Root — catch this for any tracker error."""
    exit_code: int = 1


class ExpenseNotFoundError(ExpenseTrackerError):
    def __init__(self, expense_id: int) -> None:
        self.expense_id = expense_id
        super().__init__(f"No expense found with ID {expense_id}")


class NoExpensesError(ExpenseTrackerError):
    def __init__(self, context: str = "") -> None:
        super().__init__(f"No expenses found{' ' + context if context else ''}")


class InvalidAmountError(ExpenseTrackerError):
    def __init__(self, amount: float) -> None:
        self.amount = amount
        super().__init__(f"Amount must be > 0, got {amount}")


class InvalidDateError(ExpenseTrackerError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Invalid date '{value}' — use YYYY-MM-DD")


class InvalidDateRangeError(ExpenseTrackerError):
    def __init__(self, start: str, end: str) -> None:
        super().__init__(f"Start date {start} is after end date {end}")


class InvalidCategoryError(ExpenseTrackerError):
    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(
            f"Invalid category '{category.strip()}' — must be 1-30 non-blank chars"
        )


class InvalidNameError(ExpenseTrackerError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(
            f"Invalid name '{name.strip()}' — must be 1-60 non-blank chars"
        )


class StorageError(ExpenseTrackerError):
    """Raised when the JSON file cannot be read or written."""
    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        super().__init__(f"Storage error ({path}): {reason}")
