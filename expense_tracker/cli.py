from __future__ import annotations
import argparse
import sys
from datetime import date
from functools import wraps
from typing import Callable, Any
from .tracker import ExpenseTracker
from .exceptions import ExpenseTrackerError
from .validators import parse_date
from .display import (
    print_table, print_success, print_error,
    print_summary, print_filter_header, print_info,
)


# ── Error boundary decorator ───────────────────────────────────────────────────

def _handle_errors(fn: Callable[..., None]) -> Callable[..., None]:
    """Catch any ExpenseTrackerError, show a clean message, exit 1."""
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
    tracker = ExpenseTracker()
    has_cat   = bool(args.category)
    has_start = bool(args.start)
    has_end   = bool(args.end)

    if has_cat and (has_start or has_end):
        expenses = tracker.filter_by_category_and_date(args.category, args.start, args.end)
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
    tracker = ExpenseTracker()
    expense = tracker.delete(args.id)
    print_success(f"Deleted {expense.short()}")


@_handle_errors
def cmd_summary(args: argparse.Namespace) -> None:
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
    for e in expenses:
        by_cat[e.category] = round(by_cat.get(e.category, 0) + e.amount, 2)
    by_cat = dict(sorted(by_cat.items(), key=lambda x: -x[1]))
    total = sum(expenses[i].amount for i in range(len(expenses)))

    stats = {
        "Count":         str(len(expenses)),
        "Average":       f"Rs.{total/len(expenses):,.2f}",
        "Most expensive": tracker.most_expensive().short(),
        "Least expensive": tracker.least_expensive().short(),
    }
    print_summary(by_cat, total, stats)


@_handle_errors
def cmd_info(args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()
    e = tracker.get(args.id)
    print()
    print_info("ID",       str(e.id))
    print_info("Name",     e.name)
    print_info("Amount",   e.amount_str())
    print_info("Category", e.category)
    print_info("Date",     str(e.date))
    print_info("Note",     e.note or "—")
    print()


# ── Parser ─────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense",
        description="CLI Expense Tracker — Day 25: fully polished OOP",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # add
    p = sub.add_parser("add", help="Add a new expense")
    p.add_argument("name",     type=str,   help="Expense name")
    p.add_argument("amount",   type=float, help="Amount e.g. 150.00")
    p.add_argument("category", type=str,   help="Category e.g. Food")
    p.add_argument("--date",   type=str,   help="YYYY-MM-DD (default: today)")
    p.add_argument("--note",   type=str,   help="Optional note")
    p.set_defaults(func=cmd_add)

    # update
    p = sub.add_parser("update", help="Update fields on an existing expense")
    p.add_argument("id",         type=int,   help="Expense ID to update")
    p.add_argument("--name",     type=str,   help="New name")
    p.add_argument("--amount",   type=float, help="New amount")
    p.add_argument("--category", type=str,   help="New category")
    p.add_argument("--note",     type=str,   help="New note")
    p.set_defaults(func=cmd_update)

    # view
    p = sub.add_parser("view", help="View / filter expenses")
    p.add_argument("--category", "-c", type=str, help="Filter by category")
    p.add_argument("--start",    "-s", type=str, help="From date YYYY-MM-DD")
    p.add_argument("--end",      "-e", type=str, help="Until date YYYY-MM-DD")
    p.add_argument("--sort",           type=str,
                   choices=["date","amount","id","category","name"],
                   help="Sort column (default: date)")
    p.set_defaults(func=cmd_view)

    # delete
    p = sub.add_parser("delete", help="Delete an expense by ID")
    p.add_argument("id", type=int, help="Expense ID")
    p.set_defaults(func=cmd_delete)

    # summary
    p = sub.add_parser("summary", help="Category breakdown + stats")
    p.add_argument("--start", "-s", type=str, help="From date YYYY-MM-DD")
    p.add_argument("--end",   "-e", type=str, help="Until date YYYY-MM-DD")
    p.set_defaults(func=cmd_summary)

    # info
    p = sub.add_parser("info", help="Show all fields for one expense")
    p.add_argument("id", type=int, help="Expense ID")
    p.set_defaults(func=cmd_info)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
