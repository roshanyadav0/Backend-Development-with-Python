# expense_tracker.py
from exceptions import (
    InvalidAmountError,
    DuplicateExpenseError,
    CategoryNotFoundError,
    ExpenseAppError
)
from datetime import date

class ExpenseTracker:
    def __init__(self):
        self.expenses = []   # list of dicts
        self.categories = {"food", "travel", "bills", "entertainment", "other"}

    def add_expense(self, name: str, amount: float, category: str, on: date = None):
        on = on or date.today()

        # --- Validate amount ---
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise InvalidAmountError(amount)

        if amount <= 0:
            raise InvalidAmountError(amount)

        # --- Validate category ---
        if category not in self.categories:
            raise CategoryNotFoundError(category)

        # --- Check duplicate ---
        for exp in self.expenses:
            if exp["name"].lower() == name.lower() and exp["date"] == on:
                raise DuplicateExpenseError(name, on)

        # --- All good: save ---
        self.expenses.append({
            "name": name,
            "amount": amount,
            "category": category,
            "date": on
        })
        print(f"  Added ✓  {name} | ₹{amount:.2f} | {category} | {on}")

    def show_all(self):
        if not self.expenses:
            print("  No expenses recorded.")
            return
        print(f"\n  {'Name':<20} {'Amount':>10} {'Category':<15} {'Date'}")
        print("  " + "-" * 58)
        for e in self.expenses:
            print(f"  {e['name']:<20} ₹{e['amount']:>9.2f} {e['category']:<15} {e['date']}")


def run():
    tracker = ExpenseTracker()

    # Test cases
    test_cases = [
        ("Lunch",       250,   "food"),
        ("Lunch",       250,   "food"),    # duplicate
        ("Bus Ticket",  -50,   "travel"),  # negative amount
        ("Netflix",     199,   "fun"),     # bad category
        ("Electricity", 1200,  "bills"),
        ("Coffee",      "abc", "food"),    # invalid type
    ]

    for name, amount, category in test_cases:
        try:
            tracker.add_expense(name, amount, category)

        except DuplicateExpenseError as e:
            print(f"  [DUPLICATE]  {e}")

        except InvalidAmountError as e:
            print(f"  [INVALID ₹]  {e}")

        except CategoryNotFoundError as e:
            print(f"  [BAD CAT]    {e}")

        except ExpenseAppError as e:          # catch-all for app errors
            print(f"  [APP ERROR]  {e}")

    tracker.show_all()

if __name__ == "__main__":
    run()


# Quick reference

# Define
class MyError(Exception):
    def __init__(self, value):
        super().__init__(f"Problem with: {value}")
        self.value = value          # store for access later

# Raise
raise MyError("bad input")

# Catch
try:
    ...
except MyError as e:
    print(e)          # prints the message
    print(e.value)    # access stored data