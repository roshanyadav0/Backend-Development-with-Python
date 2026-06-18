from functools import total_ordering

@total_ordering
class Expense:
    currency = "INR"

    def __init__(self, title, amount, category):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self.title    = title
        self.amount   = float(amount)
        self.category = category

    def describe(self):
        return f"{self.title} [{self.category}]: ₹{self.amount:.2f}"

    def __str__(self):   return self.describe()
    def __repr__(self):  return f"Expense('{self.title}', {self.amount}, '{self.category}')"
    def __eq__(self, other):
        if not isinstance(other, Expense): return NotImplemented
        return self.amount == other.amount
    def __lt__(self, other):
        if not isinstance(other, Expense): return NotImplemented
        return self.amount < other.amount


@total_ordering
class ExpenseCategory(Expense):
    """An Expense that also tracks a monthly budget for its category."""

    def __init__(self, title, amount, category, budget):
        super().__init__(title, amount, category)   # parent handles validation too
        self.budget  = float(budget)
        self.entries = []                           # child-only: list of sub-expenses

    # ── child-only methods ───────────────────────────────────────────
    def add_entry(self, expense):
        """Add a related Expense to this category bucket."""
        self.entries.append(expense)
        self.amount += expense.amount              # update running total

    def remaining(self):
        return self.budget - self.amount

    def is_over_budget(self):
        return self.amount > self.budget

    def summary(self):
        pct = (self.amount / self.budget) * 100 if self.budget else 0
        status = "OVER BUDGET ⚠" if self.is_over_budget() else "within budget"
        return (f"Category : {self.category}\n"
                f"Spent    : ₹{self.amount:.2f} / ₹{self.budget:.2f} ({pct:.1f}%)\n"
                f"Remaining: ₹{self.remaining():.2f}\n"
                f"Status   : {status}")

    # ── overrides ───────────────────────────────────────────────────
    def describe(self):
        base = super().describe()                  # reuse parent output
        return f"{base} | Budget ₹{self.budget:.2f}"

    def __repr__(self):
        return (f"ExpenseCategory('{self.title}', {self.amount}, "
                f"'{self.category}', budget={self.budget})")

food = ExpenseCategory("Food", 0, "Food", budget=5000)

food.add_entry(Expense("Lunch",  350, "Food"))
food.add_entry(Expense("Dinner", 820, "Food"))
food.add_entry(Expense("Snacks", 150, "Food"))

print(food.summary())
# Category : Food
# Spent    : ₹1320.00 / ₹5000.00 (26.4%)
# Remaining: ₹3680.00
# Status   : within budget

print(food.describe())
# Food [Food]: ₹1320.00 | Budget ₹5000.00

# Sorting works via inherited __lt__
cats = [
    ExpenseCategory("Transport", 2200, "Transport", 3000),
    ExpenseCategory("Food",      1320, "Food",      5000),
    ExpenseCategory("Office",    4800, "Office",    4000),
]
for c in sorted(cats):
    print(c.title, c.amount)
# Food 1320 | Transport 2200 | Office 4800