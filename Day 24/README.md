# 💰 CLI Expense Tracker

A fully typed, argparse-based command-line expense tracker. Day 23 of the Python 30-day challenge.

## Setup

```bash
python -m venv myenv
source myenv/bin/activate     # Windows: myenv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
# Add an expense
python -m expense_tracker.cli add "Coffee" 3.50 Food
python -m expense_tracker.cli add "Bus ticket" 2.00 Transport --date 2024-01-15
python -m expense_tracker.cli add "Lunch" 150.00 Food --note "Team lunch"

# View all expenses
python -m expense_tracker.cli view

# View filtered by category
python -m expense_tracker.cli view --category Food

# Delete by ID
python -m expense_tracker.cli delete 2

# Category summary
python -m expense_tracker.cli summary
```

## Project Structure

```
expense_cli/
├── expense_tracker/
│   ├── __init__.py
│   ├── models.py      # Expense dataclass
│   ├── tracker.py     # Business logic
│   ├── storage.py     # JSON persistence
│   ├── display.py     # Table / colour output
│   └── cli.py         # argparse entry point
├── requirements.txt
├── mypy.ini
└── README.md
```

## Type Check

```bash
mypy expense_tracker/
```

## Data

All expenses are saved automatically to `expenses.json` after every operation.
