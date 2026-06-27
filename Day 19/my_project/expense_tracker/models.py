# expense_tracker/models.py
from datetime import date

class Expense:
    def __init__(self, title: str, amount: float, category: str):
        self.title    = title
        self.amount   = amount
        self.category = category
        self.date     = date.today().isoformat()   # datetime stdlib

    def to_dict(self):
        return {
            "title":    self.title,
            "amount":   self.amount,
            "category": self.category,
            "date":     self.date,
        }

    def __repr__(self):
        return f"Expense({self.title!r}, ₹{self.amount}, {self.category})"