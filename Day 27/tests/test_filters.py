"""
Tests for all three filter paths:
  filter_by_category()
  filter_by_date()
  filter_by_category_and_date()

Also tests validators.date_range() directly.
"""
from __future__ import annotations
from datetime import date
import pytest
from expense_tracker.tracker import ExpenseTracker
from expense_tracker.exceptions import (
    InvalidCategoryError,
    InvalidDateError,
    InvalidDateRangeError,
    NoExpensesError,
)
from expense_tracker import validators


# ── filter_by_category ────────────────────────────────────────────────────────

class TestFilterByCategory:

    def test_returns_only_matching_category(self, loaded_tracker: ExpenseTracker) -> None:
        results = loaded_tracker.filter_by_category("Food")
        assert all(e.category == "Food" for e in results)

    def test_case_insensitive(self, loaded_tracker: ExpenseTracker) -> None:
        lower  = loaded_tracker.filter_by_category("food")
        upper  = loaded_tracker.filter_by_category("FOOD")
        titled = loaded_tracker.filter_by_category("Food")
        assert [e.id for e in lower] == [e.id for e in upper] == [e.id for e in titled]

    def test_correct_count(self, loaded_tracker: ExpenseTracker) -> None:
        # loaded_tracker has 2 Food expenses (Coffee + Groceries)
        results = loaded_tracker.filter_by_category("Food")
        assert len(results) == 2

    def test_missing_category_raises(self, loaded_tracker: ExpenseTracker) -> None:
        with pytest.raises(NoExpensesError):
            loaded_tracker.filter_by_category("Holidays")

    def test_blank_category_raises(self, loaded_tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidCategoryError):
            loaded_tracker.filter_by_category("   ")


# ── filter_by_date ────────────────────────────────────────────────────────────

class TestFilterByDate:

    @pytest.fixture
    def dated_tracker(self, tracker: ExpenseTracker) -> ExpenseTracker:
        """Tracker with expenses on known, spread-out dates."""
        tracker.add("Jan expense",  100.0, "Misc", expense_date=date(2024, 1, 10))
        tracker.add("Feb expense",  200.0, "Misc", expense_date=date(2024, 2, 15))
        tracker.add("Mar expense",  300.0, "Misc", expense_date=date(2024, 3, 20))
        return tracker

    def test_start_and_end_inclusive(self, dated_tracker: ExpenseTracker) -> None:
        results = dated_tracker.filter_by_date("2024-01-10", "2024-02-15")
        assert len(results) == 2

    def test_only_start_means_open_end(self, dated_tracker: ExpenseTracker) -> None:
        results = dated_tracker.filter_by_date(start="2024-02-01")
        assert len(results) == 2   # Feb + Mar

    def test_only_end_means_open_start(self, dated_tracker: ExpenseTracker) -> None:
        results = dated_tracker.filter_by_date(end="2024-01-31")
        assert len(results) == 1   # Jan only

    def test_no_args_returns_all(self, dated_tracker: ExpenseTracker) -> None:
        # Without args, no date filtering — all 3 returned
        results = dated_tracker.filter_by_date()
        assert len(results) == 3

    def test_bad_date_format_raises(self, dated_tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidDateError):
            dated_tracker.filter_by_date(start="01/01/2024")

    def test_start_after_end_raises(self, dated_tracker: ExpenseTracker) -> None:
        with pytest.raises(InvalidDateRangeError):
            dated_tracker.filter_by_date("2024-12-01", "2024-01-01")

    def test_no_match_raises_no_expenses(self, dated_tracker: ExpenseTracker) -> None:
        with pytest.raises(NoExpensesError):
            dated_tracker.filter_by_date("2025-01-01", "2025-12-31")


# ── filter_by_category_and_date ───────────────────────────────────────────────

class TestFilterByCategoryAndDate:

    @pytest.fixture
    def combo_tracker(self, tracker: ExpenseTracker) -> ExpenseTracker:
        tracker.add("Coffee",  3.50,  "Food",      expense_date=date(2024, 1, 5))
        tracker.add("Uber",  220.00,  "Transport", expense_date=date(2024, 1, 10))
        tracker.add("Lunch", 145.00,  "Food",      expense_date=date(2024, 2, 10))
        tracker.add("Train",  80.00,  "Transport", expense_date=date(2024, 2, 20))
        return tracker

    def test_category_and_date_combined(self, combo_tracker: ExpenseTracker) -> None:
        results = combo_tracker.filter_by_category_and_date(
            "Food", start="2024-01-01", end="2024-01-31"
        )
        assert len(results) == 1
        assert results[0].name == "Coffee"

    def test_category_matched_but_date_excludes_all(self, combo_tracker: ExpenseTracker) -> None:
        with pytest.raises(NoExpensesError):
            combo_tracker.filter_by_category_and_date(
                "Food", start="2025-01-01", end="2025-12-31"
            )


# ── validators.date_range ─────────────────────────────────────────────────────

class TestValidators:

    def test_valid_range_returns_dates(self) -> None:
        start, end = validators.date_range("2024-01-01", "2024-12-31")
        assert start == date(2024, 1, 1)
        assert end   == date(2024, 12, 31)

    def test_none_start_returns_none(self) -> None:
        start, end = validators.date_range(None, "2024-12-31")
        assert start is None
        assert end   == date(2024, 12, 31)

    def test_none_end_returns_none(self) -> None:
        start, end = validators.date_range("2024-01-01", None)
        assert start == date(2024, 1, 1)
        assert end   is None

    def test_both_none_returns_none_none(self) -> None:
        start, end = validators.date_range(None, None)
        assert start is None
        assert end   is None

    @pytest.mark.parametrize("bad", ["2024/01/01", "01-01-2024", "Jan 1 2024"])
    def test_bad_formats_raise_via_range(self, bad: str) -> None:
        """Non-empty bad formats go through date_range."""
        with pytest.raises(InvalidDateError):
            validators.date_range(bad, None)

    def test_empty_string_raises_via_parse_date(self) -> None:
        """Empty string: date_range skips it (falsy), so test parse_date directly."""
        with pytest.raises(InvalidDateError):
            validators.parse_date("")
