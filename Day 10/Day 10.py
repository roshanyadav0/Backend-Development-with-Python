#  Inheritance basics

class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

class Dog(Animal):          # Dog inherits from Animal
    def speak(self):        # override the parent method
        return "Woof!"

d = Dog("Rex")
print(d.name)       # Rex   ← inherited from Animal.__init__
print(d.speak())    # Woof! ← overridden in Dog


#  super() — calling the parent

class Expense:
    def __init__(self, title, amount, category):
        self.title    = title
        self.amount   = float(amount)
        self.category = category

class ExpenseCategory(Expense):          # child
    def __init__(self, title, amount, category, budget):
        super().__init__(title, amount, category)   # runs Expense.__init__
        self.budget = float(budget)                 # child-only attribute

# Method overriding

class Expense:
    def describe(self):
        return f"{self.title}: ₹{self.amount:.2f}"

class ExpenseCategory(Expense):
    def describe(self):                          # override
        used_pct = (self.amount / self.budget) * 100
        base = super().describe()                # reuse parent's output
        return f"{base} | Budget: ₹{self.budget:.2f} ({used_pct:.1f}% used)"

e = ExpenseCategory("Food", 1200, "Food", 3000)
print(e.describe())
# Food: ₹1200.00 | Budget: ₹3000.00 (40.0% used)

# __repr__ vs __str__
# 
# DunderWhen it firesAudienceRule of thumb__str__print(obj), str(obj), f-stringsEnd userReadable, friendly__repr__REPL, repr(obj), logs, debuggerDeveloperUnambiguous, recreatable

class Expense:
    def __str__(self):
        return f"{self.title}: ₹{self.amount:.2f}"           # user-facing

    def __repr__(self):
        return f"Expense('{self.title}', {self.amount}, '{self.category}')"  # dev-facing

e = Expense("Coffee", 4.5, "Food")
print(str(e))    # Coffee: ₹4.50
print(repr(e))   # Expense('Coffee', 4.5, 'Food')

# __eq__ and __lt__ for comparisons
# Without these, == compares memory addresses (always False for two different objects even with identical data).

class Expense:
    def __eq__(self, other):
        if not isinstance(other, Expense):
            return NotImplemented
        return self.title == other.title and self.amount == other.amount

    def __lt__(self, other):                      # enables sorted(), min(), max()
        if not isinstance(other, Expense):
            return NotImplemented
        return self.amount < other.amount

e1 = Expense("Coffee", 4.5, "Food")
e2 = Expense("Coffee", 4.5, "Food")
e3 = Expense("Uber",  12.0, "Transport")

print(e1 == e2)          # True  ← __eq__
print(e1 == e3)          # False
print(e1 < e3)           # True  ← __lt__ (4.5 < 12.0)
print(sorted([e3, e1]))  # [Coffee, Uber] sorted by amount

