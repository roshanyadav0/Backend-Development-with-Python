"""
conftest.py — pytest fixtures shared across all test files.

Fixtures are functions decorated with @pytest.fixture.
pytest injects them automatically when a test parameter name matches.

Scope:
  "function" (default) — fresh fixture for every test  ← we use this
  "module"             — one fixture for the whole file
  "session"            — one fixture for the entire test run
"""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
import pytest
from expense_tracker.tracker import ExpenseTracker


@pytest.fixture
def tmp_file(tmp_path: Path) -> Path:
    """An empty expenses JSON file in a pytest-managed temp dir."""
    f = tmp_path / "expenses.json"
    f.write_text("[]")
    return f


@pytest.fixture
def tracker(tmp_file: Path) -> ExpenseTracker:
    """A fresh ExpenseTracker backed by a temp file — isolated per test."""
    return ExpenseTracker(data_file=tmp_file)


@pytest.fixture
def loaded_tracker(tracker: ExpenseTracker) -> ExpenseTracker:
    """Tracker pre-loaded with 4 realistic expenses for filter tests."""
    tracker.add("Morning Coffee",  3.50,  "Food",          expense_date=None)
    tracker.add("Uber ride",      220.00, "Transport",     expense_date=None)
    tracker.add("Groceries",      860.00, "Food",          expense_date=None)
    tracker.add("Gym membership", 999.00, "Health",        expense_date=None)
    return tracker
