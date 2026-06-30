from __future__ import annotations
from .tracker import ExpenseTracker
from .storage import save_to_file, load_from_file

DATA_FILE = "expenses.json"


def main() -> None:
    tracker = ExpenseTracker()
    tracker.expenses = load_from_file(DATA_FILE)

    tracker.add_expense("Coffee", 3.5, "Food")
    tracker.add_expense("Bus ticket", 2.0, "Transport")

    print(f"Total spent: {tracker.total_spent():.2f}")
    print("By category:", tracker.total_by_category())

    save_to_file(tracker.expenses, DATA_FILE)


if __name__ == "__main__":
    main()
