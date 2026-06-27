# expense_tracker/reports.py
from .utils import format_currency           # relative import

def summary(expenses: list) -> None:
    if not expenses:
        print("No expenses yet.")
        return

    total = sum(e["amount"] for e in expenses)
    print(f"\n{'─'*35}")
    print(f"  Total Expenses : {format_currency(total)}")
    print(f"  No. of Records : {len(expenses)}")

    # Group by category using a plain dict
    by_cat = {}
    for e in expenses:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]

    print("\n  By Category:")
    for cat, amt in sorted(by_cat.items()):
        print(f"    {cat:<15} {format_currency(amt)}")
    print(f"{'─'*35}\n")