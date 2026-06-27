# main.py  (project root)
from expense_tracker import Expense, load_expenses, save_expenses, summary
from expense_tracker.utils import validate_amount
import sys

def add_expense():
    title    = input("Title    : ")
    amount   = validate_amount(input("Amount   : "))
    category = input("Category : ")

    exp      = Expense(title, amount, category)
    expenses = load_expenses()
    expenses.append(exp.to_dict())
    save_expenses(expenses)
    print(f"✓ Added {exp}")

def main():
    actions = {"1": add_expense, "2": lambda: summary(load_expenses())}
    print("\n1. Add Expense\n2. Summary\n3. Quit")
    choice = input("Choice: ").strip()
    if choice == "3":
        sys.exit(0)
    action = actions.get(choice)
    if action:
        action()
    else:
        print("Invalid choice.")

if __name__ == '__main__':
    main()