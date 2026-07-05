"""Command-line interface — argument parsing and command dispatch."""

from __future__ import annotations

import argparse
import sys
from functools import wraps
from typing import Callable, Any

from .display import (
    print_error,
    print_filter_header,
    print_info,
    print_success,
    print_summary,
    print_table,
)
from .exceptions import ExpenseTrackerError
from .tracker import ExpenseTracker
from .validators import parse_date

# ── Error boundary decorator ───────────────────────────────────────────────────


def _handle_errors(fn: Callable[..., None]) -> Callable[..., None]:
    """Catch any ExpenseTrackerError, print a clean message, and exit 1."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            fn(*args, **kwargs)
        except ExpenseTrackerError as exc:
            print_error(str(exc))
            sys.exit(1)

    return wrapper


# ── Sub-command handlers ───────────────────────────────────────────────────────


@_handle_errors
def cmd_add(args: argparse.Namespace) -> None:
    """Handle the ``add`` sub-command."""
    tracker = ExpenseTracker()
    expense_date = parse_date(args.date) if args.date else None
    expense = tracker.add(
        name=args.name,
        amount=args.amount,
        category=args.category,
        expense_date=expense_date,
        note=args.note,
    )
    print_success(f"Added {expense.short()} on {expense.date}")


@_handle_errors
def cmd_update(args: argparse.Namespace) -> None:
    """Handle the ``update`` sub-command."""
    tracker = ExpenseTracker()
    expense = tracker.update(
        expense_id=args.id,
        name=args.name,
        amount=args.amount,
        category=args.category,
        note=args.note,
    )
    print_success(f"Updated → {expense.short()}")


@_handle_errors
def cmd_view(args: argparse.Namespace) -> None:
    """Handle the ``view`` sub-command, applying any requested filters."""
    tracker = ExpenseTracker()
    has_cat = bool(args.category)
    has_start = bool(args.start)
    has_end = bool(args.end)

    if has_cat and (has_start or has_end):
        expenses = tracker.filter_by_category_and_date(
            args.category, args.start, args.end
        )
        print_filter_header(category=args.category, start=args.start, end=args.end)
    elif has_cat:
        expenses = tracker.filter_by_category(args.category)
        print_filter_header(category=args.category)
    elif has_start or has_end:
        expenses = tracker.filter_by_date(args.start, args.end)
        print_filter_header(start=args.start, end=args.end)
    else:
        expenses = tracker.all(sort_by=args.sort or "date")

    print_table(expenses)


@_handle_errors
def cmd_delete(args: argparse.Namespace) -> None:
    """Handle the ``delete`` sub-command."""
    tracker = ExpenseTracker()
    expense = tracker.delete(args.id)
    print_success(f"Deleted {expense.short()}")


@_handle_errors
def cmd_summary(args: argparse.Namespace) -> None:
    """Handle the ``summary`` sub-command."""
    tracker = ExpenseTracker()
    if args.start or args.end:
        expenses = tracker.filter_by_date(args.start, args.end)
        print_filter_header(start=args.start, end=args.end)
    else:
        expenses = tracker.all()

    if not expenses:
        print_error("No expenses to summarise.")
        return

    by_cat: dict[str, float] = {}
    for expense in expenses:
        by_cat[expense.category] = round(
            by_cat.get(expense.category, 0) + expense.amount, 2
        )
    by_cat = dict(sorted(by_cat.items(), key=lambda item: -item[1]))
    running_total = sum(expense.amount for expense in expenses)

    stats = {
        "Count": str(len(expenses)),
        "Average": f"Rs.{running_total / len(expenses):,.2f}",
        "Most expensive": tracker.most_expensive().short(),
        "Least expensive": tracker.least_expensive().short(),
    }
    print_summary(by_cat, running_total, stats)


@_handle_errors
def cmd_info(args: argparse.Namespace) -> None:
    """Handle the ``info`` sub-command."""
    tracker = ExpenseTracker()
    expense = tracker.get(args.id)
    print()
    print_info("ID", str(expense.id))
    print_info("Name", expense.name)
    print_info("Amount", expense.amount_str())
    print_info("Category", expense.category)
    print_info("Date", str(expense.date))
    print_info("Note", expense.note or "—")
    print()


# ── Parser ─────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser with all sub-commands."""
    parser = argparse.ArgumentParser(
        prog="expense",
        description="CLI Expense Tracker — Day 27: code quality pass",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # add
    parser_add = sub.add_parser("add", help="Add a new expense")
    parser_add.add_argument("name", type=str, help="Expense name")
    parser_add.add_argument("amount", type=float, help="Amount e.g. 150.00")
    parser_add.add_argument("category", type=str, help="Category e.g. Food")
    parser_add.add_argument("--date", type=str, help="YYYY-MM-DD (default: today)")
    parser_add.add_argument("--note", type=str, help="Optional note")
    parser_add.set_defaults(func=cmd_add)

    # update
    parser_upd = sub.add_parser("update", help="Update fields on an existing expense")
    parser_upd.add_argument("id", type=int, help="Expense ID to update")
    parser_upd.add_argument("--name", type=str, help="New name")
    parser_upd.add_argument("--amount", type=float, help="New amount")
    parser_upd.add_argument("--category", type=str, help="New category")
    parser_upd.add_argument("--note", type=str, help="New note")
    parser_upd.set_defaults(func=cmd_update)

    # view
    parser_view = sub.add_parser("view", help="View / filter expenses")
    parser_view.add_argument("--category", "-c", type=str, help="Filter by category")
    parser_view.add_argument("--start", "-s", type=str, help="From date YYYY-MM-DD")
    parser_view.add_argument("--end", "-e", type=str, help="Until date YYYY-MM-DD")
    parser_view.add_argument(
        "--sort",
        type=str,
        choices=["date", "amount", "id", "category", "name"],
        help="Sort column (default: date)",
    )
    parser_view.set_defaults(func=cmd_view)

    # delete
    parser_del = sub.add_parser("delete", help="Delete an expense by ID")
    parser_del.add_argument("id", type=int, help="Expense ID")
    parser_del.set_defaults(func=cmd_delete)

    # summary
    parser_sum = sub.add_parser("summary", help="Category breakdown + stats")
    parser_sum.add_argument("--start", "-s", type=str, help="From date YYYY-MM-DD")
    parser_sum.add_argument("--end", "-e", type=str, help="Until date YYYY-MM-DD")
    parser_sum.set_defaults(func=cmd_summary)

    # info
    parser_info = sub.add_parser("info", help="Show all fields for one expense")
    parser_info.add_argument("id", type=int, help="Expense ID")
    parser_info.set_defaults(func=cmd_info)

    return parser


def main() -> None:
    """Entry point: parse arguments and dispatch to the appropriate handler."""
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
