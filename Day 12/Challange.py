import os

FILENAME = "expenses.txt"

def save_expenses(expenses: list[dict]) -> None:
    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write("===== Expense Report =====\n")
        total = 0
        for exp in expenses:
            line = f"{exp['name']:<20} ₹{exp['amount']:>8.2f}\n"
            f.write(line)
            total += exp["amount"]
        f.write("-" * 30 + "\n")
        f.write(f"{'TOTAL':<20} ₹{total:>8.2f}\n")
    print(f"Saved to '{FILENAME}'")

def load_expenses() -> None:
    if not os.path.isfile(FILENAME):
        print("No expense file found.")
        return
    with open(FILENAME, "r", encoding="utf-8") as f:
        print(f.read())

# ── Demo ──────────────────────────────────────
expenses = [
    {"name": "Groceries",   "amount": 1200.00},
    {"name": "Electricity", "amount":  850.50},
    {"name": "Internet",    "amount":  699.00},
    {"name": "Petrol",      "amount":  500.00},
]

save_expenses(expenses)
load_expenses()