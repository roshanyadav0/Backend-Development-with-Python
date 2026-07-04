"""
Day 26 — Part 1: raw assert-based tests.

These run fine with plain `python` — no pytest needed.
But pytest also collects and runs them, giving nicer output.

Concept: assert <condition>, "message shown if False"
If condition is False → AssertionError is raised → test fails.
"""
from __future__ import annotations
from pathlib import Path
import tempfile
import sys

# Make sure the package is importable when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from expense_tracker.tracker import ExpenseTracker
from expense_tracker.exceptions import (
    InvalidAmountError,
    InvalidNameError,
    InvalidCategoryError,
)


def _tracker() -> ExpenseTracker:
    """Helper: fresh tracker backed by a temp file (no side effects)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    Path(tmp.name).write_text("[]")
    return ExpenseTracker(data_file=Path(tmp.name))


# ── 5 raw assert tests ────────────────────────────────────────────────────────

def test_assert_1_expense_is_added() -> None:
    """Adding an expense increases the count by 1."""
    tracker = _tracker()
    before = tracker.count
    tracker.add("Coffee", 3.50, "Food")
    assert tracker.count == before + 1, "count should grow by 1 after add()"


def test_assert_2_amount_is_stored_correctly() -> None:
    """Amount stored must equal the value passed in."""
    tracker = _tracker()
    expense = tracker.add("Book", 299.00, "Education")
    assert expense.amount == 299.00, f"expected 299.00, got {expense.amount}"


def test_assert_3_total_accumulates() -> None:
    """Total must equal the sum of all added amounts."""
    tracker = _tracker()
    tracker.add("Coffee", 3.50, "Food")
    tracker.add("Bus",   20.00, "Transport")
    tracker.add("Lunch", 80.00, "Food")
    assert tracker.total == 103.50, f"expected 103.50, got {tracker.total}"


def test_assert_4_delete_removes_expense() -> None:
    """After delete(), the expense ID must not be present."""
    tracker = _tracker()
    exp = tracker.add("Netflix", 199.00, "Entertainment")
    tracker.delete(exp.id)
    assert exp.id not in tracker, f"ID {exp.id} still found after delete()"


def test_assert_5_category_is_title_cased() -> None:
    """Validator must title-case the category regardless of input."""
    tracker = _tracker()
    exp = tracker.add("Gym", 999.00, "HEALTH")
    assert exp.category == "Health", f"expected 'Health', got '{exp.category}'"


# ── Run directly: python tests/test_asserts.py ────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_assert_1_expense_is_added,
        test_assert_2_amount_is_stored_correctly,
        test_assert_3_total_accumulates,
        test_assert_4_delete_removes_expense,
        test_assert_5_category_is_title_cased,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
