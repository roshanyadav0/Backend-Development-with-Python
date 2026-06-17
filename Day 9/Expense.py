from datetime import date

class Expense:
    """Tracks a single financial expense."""

    currency = "INR"             # Class attribute: shared default
    _all_expenses = []           # Class attribute: registry of all instances

    def __init__(self, title, amount, category, date_=None):
        if amount < 0:
            raise ValueError("Amount cannot be negative.")
        self.title = title
        self.amount = float(amount)
        self.category = category
        self.date = date_ or date.today()    # Default to today if not given
        Expense._all_expenses.append(self)   # Register this expense globally

    # ── Instance methods ────────────────────────────────────────────────

    def describe(self):
        return (f"[{self.date}] {self.title} | "
                f"{self.category} | {self.currency} {self.amount:.2f}")

    def apply_tax(self, rate=0.18):
        """Return amount with tax included."""
        return round(self.amount * (1 + rate), 2)

    def update_amount(self, new_amount):
        """Safely update the expense amount."""
        if new_amount < 0:
            raise ValueError("Amount cannot be negative.")
        self.amount = float(new_amount)

    def to_dict(self):
        """Serialize to a dictionary (useful for JSON export)."""
        return {
            "title": self.title,
            "amount": self.amount,
            "category": self.category,
            "date": str(self.date),
        }

    # ── Class methods — operate on the class, not an instance ───────────

    @classmethod
    def total_spent(cls):
        """Sum of all expense amounts ever created."""
        return sum(e.amount for e in cls._all_expenses)

    @classmethod
    def by_category(cls, category):
        """Return all expenses matching a category."""
        return [e for e in cls._all_expenses if e.category == category]

    # ── Static method — utility that doesn't need self or cls ───────────

    @staticmethod
    def is_valid_amount(value):
        """Check if a value is a valid positive number."""
        return isinstance(value, (int, float)) and value > 0

    # ── Dunder methods — make objects feel native in Python ─────────────

    def __repr__(self):
        return f"Expense('{self.title}', {self.amount}, '{self.category}')"

    def __str__(self):
        return self.describe()
    
    def __lt__(self, other):
        """Allows sorting Expense objects by amount."""
        return self.amount < other.amount
    


# Instantiate
e1 = Expense("Coffee", 4.50, "Food")
e2 = Expense("Gym Membership", 1500, "Health")
e3 = Expense("React Course", 3200, "Education")
e4 = Expense("Dinner", 850, "Food")

# Instance methods
print(e1)                     # [2026-06-17] Coffee | Food | INR 4.50
print(e3.apply_tax())         # 3776.0
print(e1.to_dict())

# Class methods
print(Expense.total_spent())             # 5554.5
food = Expense.by_category("Food")
for f in food: print(f)

# Static method
print(Expense.is_valid_amount(-5))       # False
print(Expense.is_valid_amount(250))      # True

# Sorting works because we defined __lt__
all_exp = [e1, e2, e3, e4]
sorted_exp = sorted(all_exp)
for e in sorted_exp:
    print(e.title, e.amount)