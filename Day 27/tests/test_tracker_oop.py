"""
Tests for OOP features:
  properties: .count, .total, .categories, .average
  dunder methods: len(), repr(), `in` operator
  aggregates: most_expensive(), least_expensive(), total_by_category()
  sort: .all(sort_by=...)
  update: .update()
"""
from __future__ import annotations
import pytest
from expense_tracker.tracker import ExpenseTracker
from expense_tracker.exceptions import ExpenseNotFoundError, NoExpensesError


# ── Properties & dunders ──────────────────────────────────────────────────────

class TestProperties:

    def test_count_zero_on_empty(self, tracker: ExpenseTracker) -> None:
        assert tracker.count == 0

    def test_total_zero_on_empty(self, tracker: ExpenseTracker) -> None:
        assert tracker.total == 0.0

    def test_categories_unique_and_sorted(self, tracker: ExpenseTracker) -> None:
        tracker.add("a", 1.0, "Food")
        tracker.add("b", 2.0, "food")      # same category, different case
        tracker.add("c", 3.0, "Transport")
        cats = tracker.categories
        assert cats == sorted(set(cats))   # sorted + unique
        assert len(cats) == 2              # "food"→"Food" deduped

    def test_average(self, tracker: ExpenseTracker) -> None:
        tracker.add("A", 10.0, "Misc")
        tracker.add("B", 20.0, "Misc")
        tracker.add("C", 30.0, "Misc")
        assert tracker.average == 20.0

    def test_average_empty_returns_zero(self, tracker: ExpenseTracker) -> None:
        assert tracker.average == 0.0

    def test_len(self, tracker: ExpenseTracker) -> None:
        tracker.add("A", 1.0, "Misc")
        tracker.add("B", 2.0, "Misc")
        assert len(tracker) == 2

    def test_contains_true(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        assert exp.id in tracker

    def test_contains_false(self, tracker: ExpenseTracker) -> None:
        assert 999 not in tracker

    def test_repr(self, tracker: ExpenseTracker) -> None:
        tracker.add("Coffee", 3.50, "Food")
        r = repr(tracker)
        assert "ExpenseTracker" in r
        assert "expenses=1"     in r


# ── Aggregates ────────────────────────────────────────────────────────────────

class TestAggregates:

    def test_most_expensive(self, loaded_tracker: ExpenseTracker) -> None:
        exp = loaded_tracker.most_expensive()
        assert exp.name == "Gym membership"   # 999.00

    def test_least_expensive(self, loaded_tracker: ExpenseTracker) -> None:
        exp = loaded_tracker.least_expensive()
        assert exp.name == "Morning Coffee"   # 3.50

    def test_most_expensive_empty_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(NoExpensesError):
            tracker.most_expensive()

    def test_total_by_category(self, loaded_tracker: ExpenseTracker) -> None:
        by_cat = loaded_tracker.total_by_category()
        assert "Food" in by_cat
        assert "Transport" in by_cat
        # Food = 3.50 + 860.00 = 863.50
        assert by_cat["Food"] == pytest.approx(863.50)

    def test_total_by_category_sorted_descending(self, loaded_tracker: ExpenseTracker) -> None:
        by_cat = loaded_tracker.total_by_category()
        values = list(by_cat.values())
        assert values == sorted(values, reverse=True)


# ── Sort ──────────────────────────────────────────────────────────────────────

class TestSort:

    def test_sort_by_amount(self, loaded_tracker: ExpenseTracker) -> None:
        results = loaded_tracker.all(sort_by="amount")
        amounts = [e.amount for e in results]
        assert amounts == sorted(amounts)

    def test_sort_by_name(self, loaded_tracker: ExpenseTracker) -> None:
        results = loaded_tracker.all(sort_by="name")
        names = [e.name for e in results]
        assert names == sorted(names)

    def test_unknown_sort_falls_back_to_id(self, loaded_tracker: ExpenseTracker) -> None:
        results = loaded_tracker.all(sort_by="invalid_key")
        ids = [e.id for e in results]
        assert ids == sorted(ids)


# ── Update ────────────────────────────────────────────────────────────────────

class TestUpdate:

    def test_update_name(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        updated = tracker.update(exp.id, name="Flat White")
        assert updated.name == "Flat White"

    def test_update_amount(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        tracker.update(exp.id, amount=5.00)
        assert tracker.get(exp.id).amount == 5.00

    def test_update_only_specified_fields(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Coffee", 3.50, "Food")
        tracker.update(exp.id, amount=5.00)
        # name and category should be unchanged
        assert tracker.get(exp.id).name     == "Coffee"
        assert tracker.get(exp.id).category == "Food"

    def test_update_invalid_id_raises(self, tracker: ExpenseTracker) -> None:
        with pytest.raises(ExpenseNotFoundError):
            tracker.update(999, name="Ghost")

    def test_update_total_reflects_new_amount(self, tracker: ExpenseTracker) -> None:
        exp = tracker.add("Item", 100.0, "Misc")
        tracker.update(exp.id, amount=200.0)
        assert tracker.total == 200.0
