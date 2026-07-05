"""
Tests for ExpenseTracker.add() — happy paths + every validation error.

pytest style:
  - Function names start with test_
  - Use plain assert — pytest rewrites the bytecode to show detailed diffs
  - Use pytest.raises(ExcType) to assert an exception IS raised
"""
from __future__ import annotations
from datetime import date
import pytest
from expense_tracker.tracker import ExpenseTracker
from expense_tracker.exceptions import (
    InvalidAmountError,
    InvalidNameError,
    InvalidCategoryError,
)


# ── Happy paths ───────────────────────────────────────────────────────────────

class TestAddHappyPath:

    def test_returns_expense_with_correct_fields(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        assert exp.name     == "Coffee"
        assert exp.amount   == 3.50
        assert exp.category == "Food"

    def test_id_starts_at_1(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("First", 10.0, "Misc")
        assert exp.id == 1

    def test_ids_increment(self, tracker: ExpenseTracker) -> None:
        a = tracker.add("First",  10.0, "Misc")
        b = tracker.add("Second", 20.0, "Misc")
        c = tracker.add("Third",  30.0, "Misc")
        assert [a.id, b.id, c.id] == [1, 2, 3]

    def test_count_grows(self, tracker: ExpenseTracker) -> None:
        assert tracker.count == 0
        tracker.add("A", 1.0, "Misc")
        assert tracker.count == 1
        tracker.add("B", 2.0, "Misc")
        assert tracker.count == 2

    def test_default_date_is_today(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        assert exp.date == date.today()

    def test_explicit_date_is_stored(self, tracker: ExpenseTracker) -> None:
        d = date(2024, 1, 15)
        exp = tracker.add("Coffee", 3.50, "Food", expense_date=d)
        assert exp.date == d

    def test_note_is_stored(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Lunch", 120.0, "Food", note="Team lunch")
        assert exp.note == "Team lunch"

    def test_note_is_none_by_default(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        assert exp.note is None

    def test_category_is_title_cased(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Gym", 999.0, "HEALTH")
        assert exp.category == "Health"

    def test_name_is_stripped(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("  Coffee  ", 3.50, "Food")
        assert exp.name == "Coffee"

    def test_amount_is_rounded_to_2dp(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Item", 1.999, "Misc")
        assert exp.amount == 2.00

    def test_persisted_to_file(self, tracker: ExpenseTracker, tmp_file) -> None:  # type: ignore[no-untyped-def]
        """Adding an expense must immediately write to disk."""
        import json
        tracker.add("Coffee", 3.50, "Food")
        data = json.loads(tmp_file.read_text())
        assert len(data) == 1
        assert data[0]["name"] == "Coffee"


# ── Validation errors ─────────────────────────────────────────────────────────

class TestAddValidation:

    def test_negative_amount_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidAmountError):
            tracker.add("Coffee", -1.0, "Food")

    def test_zero_amount_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidAmountError):
            tracker.add("Coffee", 0.0, "Food")

    def test_blank_name_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidNameError):
            tracker.add("   ", 10.0, "Food")

    def test_empty_name_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidNameError):
            tracker.add("", 10.0, "Food")

    def test_name_too_long_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidNameError):
            tracker.add("x" * 61, 10.0, "Food")

    def test_blank_category_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidCategoryError):
            tracker.add("Coffee", 10.0, "   ")

    def test_category_too_long_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidCategoryError):
            tracker.add("Coffee", 10.0, "c" * 31)

    def test_failed_add_does_not_change_count(self, tracker: ExpenseTracker) -> None:
        """A validation failure must leave the tracker unchanged."""
        try:
            tracker.add("Coffee", -5.0, "Food")
        except InvalidAmountError:
            pass
        assert tracker.count == 0

    @pytest.mark.parametrize("amount", [-100, -0.01, 0, -999.99])
    def test_invalid_amounts_parametrized(
        self, tracker: ExpenseTracker, amount: float
    ) -> None:
        """Parametrize runs the same assertion for multiple inputs."""
        with pytest.raises(InvalidAmountError):
            tracker.add("Test", amount, "Misc")
