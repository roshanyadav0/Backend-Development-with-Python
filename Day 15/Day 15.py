# Define custom exception 

# Basic custom exception
class AppError(Exception):
    """Base exception for this app."""
    pass

# Subclass with a custom message
class InvalidAmountError(Exception):
    def __init__(self, amount):
        super().__init__(f"Invalid amount: '{amount}'. Must be a positive number.")
        self.amount = amount   # store for later use if needed

# Subclass with multiple details
class DuplicateExpenseError(Exception):
    def __init__(self, name, date):
        super().__init__(f"Expense '{name}' on {date} already exists.")
        self.name = name
        self.date = date


# Raise and Catch Custom Exceptions

def add_expense(amount, name):
    if amount <= 0:
        raise InvalidAmountError(amount)
    print(f"Added: {name} - ₹{amount}")

try:
    add_expense(-500, "Lunch")

except InvalidAmountError as e:
    print(f"[ERROR] {e}")
    print(f"  Bad value was: {e.amount}")   # access stored attribute


# Exception Hierarchy (Best Practice)

# One base → all app errors share a parent
class ExpenseAppError(Exception):
    """Root exception for Expense Tracker."""
    pass

class InvalidAmountError(ExpenseAppError):
    def __init__(self, amount):
        super().__init__(f"Amount must be positive. Got: {amount!r}")
        self.amount = amount

class DuplicateExpenseError(ExpenseAppError):
    def __init__(self, name, date):
        super().__init__(f"'{name}' on {date} is already recorded.")
        self.name = name
        self.date = date

class CategoryNotFoundError(ExpenseAppError):
    def __init__(self, category):
        super().__init__(f"Category '{category}' does not exist.")
        self.category = category


