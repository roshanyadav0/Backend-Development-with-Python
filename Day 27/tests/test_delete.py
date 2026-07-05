"""
Tests for ExpenseTracker.delete() and .get().
"""
from __future__ import annotations
import pytest
from expense_tracker.tracker import ExpenseTracker
from expense_tracker.exceptions import ExpenseNotFoundError


class TestDelete:

    def test_delete_reduces_count(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        tracker.delete(exp.id)
        assert tracker.count == 0

    def test_delete_returns_the_expense(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        deleted = tracker.delete(exp.id)
        assert deleted.id   == exp.id
        assert deleted.name == exp.name

    def test_deleted_id_not_in_tracker(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        tracker.delete(exp.id)
        assert exp.id not in tracker         # uses __contains__

    def test_delete_wrong_id_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(ExpenseNotFoundError):
            tracker.delete(999)

    def test_delete_only_removes_target(self, tracker: ExpenseTracker) -> None:
        """Deleting one expense must not affect others."""
        a = tracker.add("Coffee", 3.50, "Food")
        b = tracker.add("Uber",  220.0, "Transport")
        c = tracker.add("Gym",   999.0, "Health")
        tracker.delete(b.id)
        assert tracker.count == 2
        assert a.id in tracker
        assert c.id in tracker
        assert b.id not in tracker

    def test_ids_not_reused_after_delete(self, tracker: ExpenseTracker) -> None:
        """
        IDs increment from max(existing) + 1.
        With 2 expenses, delete the first — the next ID comes from the
        surviving expense's ID, not from 0.
        """
        a = tracker.add("First",  10.0, "Misc")   # id=1
        b = tracker.add("Second", 20.0, "Misc")   # id=2
        tracker.delete(a.id)                       # remove id=1; id=2 survives
        c = tracker.add("Third",  30.0, "Misc")   # next = max(2)+1 = 3
        assert c.id == 3
        assert c.id != a.id

    def test_total_updates_after_delete(self, tracker: ExpenseTracker) -> None:
        a = tracker.add("Coffee", 10.0, "Food")
        tracker.add("Uber", 50.0, "Transport")
        tracker.delete(a.id)
        assert tracker.total == 50.0

    def test_delete_persists_to_file(self, tracker: ExpenseTracker, tmp_file) -> None:  # type: ignore[no-untyped-def]
        import json
        exp = tracker.add("Coffee", 3.50, "Food")
        tracker.delete(exp.id)
        data = json.loads(tmp_file.read_text())
        assert data == []


class TestGet:

    def test_get_returns_correct_expense(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        fetched = tracker.get(exp.id)
        assert fetched.id   == exp.id
        assert fetched.name == "Coffee"

    def test_get_missing_id_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(ExpenseNotFoundError) as exc_info:
            tracker.get(42)
        assert "42" in str(exc_info.value)   # error message contains the ID
