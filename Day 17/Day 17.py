# Core Concept: The Integration Pattern

import json

# Read JSON → Filter with Comprehensions → Handle Errors
def load_expenses(filepath):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)                          # File I/O
        return [e for e in data if e["amount"] > 0]     # Comprehension
    except FileNotFoundError:
        print("File not found!")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON!")
        return []

# Exercise 1 Read JSON + Comprehension filter

# Filter only 'food' expenses from a JSON file
def get_food_expenses(path):
    try:
        with open(path) as f:
            data = json.load(f)
        return [Expense(e["title"], e["amount"], e["category"])
                for e in data if e["category"] == "food"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as err:
        print(f"Error: {err}")
        return []

# Exercise 2 Write expenses to JSON with error handling

def save_expenses(expenses: list, path: str):
    try:
        with open(path, "w") as f:
            json.dump([e.to_dict() for e in expenses], f, indent=2)
        print("Saved successfully!")
    except IOError as e:
        print(f"Could not save: {e}")

# Exercise 3 — Dict comprehension: category totals

def totals_by_category(expenses: list) -> dict:
    categories = {e.category for e in expenses}            # set comprehension
    return {
        cat: sum(e.amount for e in expenses if e.category == cat)
        for cat in categories                              # dict comprehension
    }

# Exercise 4 — Safe expense creation from raw dicts

def parse_expenses(raw: list) -> list:
    expenses = []
    for item in raw:
        try:
            expenses.append(Expense(item["title"], item["amount"], item["category"]))
        except (ValueError, KeyError) as e:
            print(f"Skipping bad entry {item}: {e}")   # error handling per item
    return expenses

# Exercise 5 — Edge case checker (deploy review)

def validate_all(path: str):
    try:
        with open(path) as f:
            raw = json.load(f)

        if not isinstance(raw, list):
            raise TypeError("Expected a list of expenses")

        valid   = [r for r in raw if isinstance(r.get("amount"), (int, float)) and r["amount"] > 0]
        invalid = [r for r in raw if r not in valid]

        print(f"✅ Valid: {len(valid)} | ❌ Skipped: {len(invalid)}")
        return parse_expenses(valid)

    except FileNotFoundError:
        print("❌ File missing")
    except json.JSONDecodeError:
        print("❌ Corrupt JSON")
    except TypeError as e:
        print(f"❌ Structure error: {e}")
    return []
