# expense_tracker/storage.py
import json
from pathlib import Path          # pathlib stdlib

DATA_FILE = Path("data/expenses.json")

def load_expenses() -> list:
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text())

def save_expenses(expenses: list) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(expenses, indent=2))