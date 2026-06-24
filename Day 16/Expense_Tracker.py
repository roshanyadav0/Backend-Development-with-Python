# expense_filters.py

expenses = [
    {"name": "Lunch",       "amount": 250,  "category": "food",          "date": "2025-01-15"},
    {"name": "Bus Ticket",  "amount": 80,   "category": "travel",        "date": "2025-01-15"},
    {"name": "Netflix",     "amount": 199,  "category": "entertainment", "date": "2025-01-14"},
    {"name": "Electricity", "amount": 1200, "category": "bills",         "date": "2025-01-14"},
    {"name": "Coffee",      "amount": 60,   "category": "food",          "date": "2025-01-13"},
    {"name": "Gym",         "amount": 500,  "category": "health",        "date": "2025-01-13"},
]

# ─── BEFORE: plain loops ────────────────────────────────────────────────────

def get_by_category_old(expenses, category):
    result = []
    for e in expenses:
        if e["category"] == category:
            result.append(e)
    return result

def get_above_amount_old(expenses, threshold):
    result = []
    for e in expenses:
        if e["amount"] > threshold:
            result.append(e)
    return result

def get_names_old(expenses):
    result = []
    for e in expenses:
        result.append(e["name"].title())
    return result

# ─── AFTER: comprehensions ───────────────────────────────────────────────────

# List comprehension — filter by category
def get_by_category(expenses, category):
    return [e for e in expenses if e["category"] == category]

# List comprehension — filter by amount
def get_above_amount(expenses, threshold):
    return [e for e in expenses if e["amount"] > threshold]

# List comprehension — transform names
def get_names(expenses):
    return [e["name"].title() for e in expenses]

# Dict comprehension — name → amount map
def name_amount_map(expenses):
    return {e["name"]: e["amount"] for e in expenses}

# Dict comprehension — category → total spent
def total_by_category(expenses):
    categories = {e["category"] for e in expenses}
    return {
        cat: sum(e["amount"] for e in expenses if e["category"] == cat)
        for cat in categories
    }

# Set comprehension — unique categories used
def unique_categories(expenses):
    return {e["category"] for e in expenses}

# List comprehension — label each expense
def label_expenses(expenses, threshold=200):
    return [
        f"{e['name']} → {'high' if e['amount'] > threshold else 'low'}"
        for e in expenses
    ]

# Dict comprehension — filter + reshape in one step
def expensive_summary(expenses, threshold=200):
    return {
        e["name"]: e["amount"]
        for e in expenses
        if e["amount"] > threshold
    }


# ─── Run & display ───────────────────────────────────────────────────────────

print("── Food expenses ──")
for e in get_by_category(expenses, "food"):
    print(f"  {e['name']:<15} ₹{e['amount']}")

print("\n── Above ₹200 ──")
for e in get_above_amount(expenses, 200):
    print(f"  {e['name']:<15} ₹{e['amount']}")

print("\n── All names ──")
print(" ", get_names(expenses))

print("\n── Name → Amount map ──")
for name, amt in name_amount_map(expenses).items():
    print(f"  {name:<15} ₹{amt}")

print("\n── Total by category ──")
for cat, total in sorted(total_by_category(expenses).items()):
    print(f"  {cat:<15} ₹{total}")

print("\n── Unique categories ──")
print(" ", unique_categories(expenses))

print("\n── Labels ──")
for label in label_expenses(expenses):
    print(f"  {label}")

print("\n── Expensive summary (>₹200) ──")
for name, amt in expensive_summary(expenses).items():
    print(f"  {name:<15} ₹{amt}")