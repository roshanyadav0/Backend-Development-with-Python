# Expense Tracker

A simple command-line expense tracker built in Python, with full type hints
and a proper package structure.

## Features
- Add, retrieve, and delete expenses
- Totals by category
- Persistent storage via JSON
- Fully type-annotated (mypy clean)

## Project Structure
```
expense_tracker/
├── __init__.py
├── models.py     # Expense dataclass
├── tracker.py    # Core business logic
├── storage.py    # Save/load to JSON
└── cli.py        # Entry point
```

## Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd expense_tracker_project

# 2. Create and activate a virtual environment
python -m venv myenv
source myenv/bin/activate    # Windows: myenv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python -m expense_tracker.cli
```

## Development

Run type checking:
```bash
mypy expense_tracker/
```

## Requirements
- Python 3.10+
