import json

# ── Expense class ──────────────────────────────────────────
class Expense:
    def __init__(self, title, amount, category):
        self.title    = title
        self.amount   = amount
        self.category = category

    def to_dict(self):
        """Convert object → dict so json.dump() can handle it."""
        return {
            "title":    self.title,
            "amount":   self.amount,
            "category": self.category
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild an Expense object from a dict (after loading JSON)."""
        return cls(data["title"], data["amount"], data["category"])

    def __repr__(self):
        return f"Expense({self.title}, ₹{self.amount}, {self.category})"


# ── Save list of expenses ──────────────────────────────────
def save_expenses(expenses, filepath="expenses.json"):
    with open(filepath, "w") as f:
        json.dump([e.to_dict() for e in expenses], f, indent=4)
    print("Expenses saved!")


# ── Load list of expenses ──────────────────────────────────
def load_expenses(filepath="expenses.json"):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            return [Expense.from_dict(d) for d in data]

    except FileNotFoundError:
        print("No saved expenses found.")
        return []

    except json.JSONDecodeError:
        print("Corrupt file. Starting fresh.")
        return []


# ── Demo ───────────────────────────────────────────────────
expenses = [
    Expense("Coffee",  50,  "Food"),
    Expense("Bus",     20,  "Travel"),
    Expense("Netflix", 199, "Entertainment"),
]

save_expenses(expenses)          # writes expenses.json

loaded = load_expenses()         # reads it back
for e in loaded:
    print(e)