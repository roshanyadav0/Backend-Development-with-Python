# Class 

# Defining  a class and __init__ method

class Expense : 
    # __INIT__ is the "constructor " runs automatically  when  you create  and object 
    # "Self " refers to specific instance being created
    def __init__(self,title,amount,category):
        self.title = title
        self.amount = amount
        self.category = category

# instanting objects 

# creating 2 distant expense objects  from  the same class
e1 = Expense("Cofee",4.50,"Food")
e2 = Expense("Uber",12.00,"Transpoart")

print(e1.title)
print(e2.amount)


# instance attribute vs class attributes

class Expense:
    currency = "INR"           # CLASS attribute — shared by ALL instances
    total_expenses = 0         # CLASS attribute — a counter shared across all

    def __init__(self, title, amount, category):
        self.title = title     # INSTANCE attribute — unique per object
        self.amount = amount
        self.category = category
        Expense.total_expenses += 1   # Modify the class attribute via class name

e1 = Expense("Coffee", 4.50, "Food")
e2 = Expense("Uber", 12.00, "Transport")

print(e1.currency)          # INR  (accessed through instance — falls back to class)
print(Expense.currency)     # INR  (accessed directly on the class)
print(Expense.total_expenses)  # 2
print(e1.total_expenses)
# NOTE - use instance attributes for data that varies per object. Use class attributes for data shared across all instances (defaults, counters, config).


# instance method & self

class Expense : 
    currency  = "INR"

    def __init__(self,title,amount,category):
        self.title = title
        self.amount = amount
        self.category = category

    # Instance method — 'self' gives access to this specific object's data

    def describe(self) : 
        return f"{self.title} {self.category} : {self.currency} {self.amount:.2f}"

    def apply_tax(self,rate = 0.18) :
        """Return the amount with gst applied"""
        return self.amount*(1+rate)
    
    def is_large(self,threashold = 1000) : 
        return self.amount > threashold
    
e = Expense("Laptop Stand", 2500, "Office")
print(e.describe())          # Laptop Stand (Office): INR 2500.00
print(e.apply_tax())         # 2950.0
print(e.is_large())          # True