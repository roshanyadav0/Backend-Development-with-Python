from __future__ import annotations
import argparse
import sys
from datetime import date
from .tracker import ExpenseTracker
from .exceptions import ExpenseTrackerError, InvalidDateError
from .filters import parse_date
from .display import (
    print_table,
    print_success,
    print_error,
    print_summary,
    print_filter_header,
)


# ── Error boundary — wraps every command ──────────────────────────────────────

def _run(fn):  # type: ignore[no-untyped-def]
    """Decorator: catch ExpenseTrackerError and exit cleanly."""
    def wrapper(args: argparse.Namespace) -> None:
        try:
            fn(args)
        except ExpenseTrackerError as e:
            print_error(str(e))
            sys.exit(1)
    return wrapper


# ── Sub-command handlers ───────────────────────────────────────────────────────

@_run
def cmd_add(args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()

    expense_date: date | None = None
    if args.date:
        expense_date = parse_date(args.date)   # raises InvalidDateError if bad

    expense = tracker.add(
        name=args.name,
        amount=args.amount,
        category=args.category,
        expense_date=expense_date,
        note=args.note,
    )
    print_success(
        f"Added expense #{expense.id}: '{expense.name}' "
        f"Rs.{expense.amount:,.2f} [{expense.category}] on {expense.date}"
    )


@_run
def cmd_view(args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()

    has_category = bool(args.category)
    has_start    = bool(args.start)
    has_end      = bool(args.end)

    # Choose the right filter based on which flags were given
    if has_category and (has_start or has_end):
        expenses = tracker.filter_by_category_and_date(
            args.category, args.start, args.end
        )
        print_filter_header(category=args.category, start=args.start, end=args.end)

    elif has_category:
        expenses = tracker.filter_by_category(args.category)
        print_filter_header(category=args.category)

    elif has_start or has_end:
        expenses = tracker.filter_by_date(args.start, args.end)
        print_filter_header(start=args.start, end=args.end)

    else:
        expenses = tracker.all()

    print_table(expenses)


@_run
def cmd_delete(args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()
    expense = tracker.delete(args.id)    # raises ExpenseNotFoundError if missing
    print_success(f"Deleted expense #{expense.id}: '{expense.name}'")


@_run
def cmd_summary(args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()

    # Summary can also be filtered by date range
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
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
    total = sum(e.amount for e in expenses)
    print_summary(by_cat, total)


# ── Parser setup ──────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense",
        description="CLI Expense Tracker — Day 24: filters & error handling",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── add ──────────────────────────────────────────────────────────────
    add_p = sub.add_parser("add", help="Add a new expense")
    add_p.add_argument("name",     type=str,   help="Expense name")
    add_p.add_argument("amount",   type=float, help="Amount e.g. 3.50")
    add_p.add_argument("category", type=str,   help="Category e.g. Food")
    add_p.add_argument("--date",   type=str,   help="Date YYYY-MM-DD (default: today)")
    add_p.add_argument("--note",   type=str,   help="Optional note")
    add_p.set_defaults(func=cmd_add)

    # ── view ─────────────────────────────────────────────────────────────
    view_p = sub.add_parser("view", help="View / filter expenses")
    view_p.add_argument("--category", "-c", type=str, help="Filter by category")
    view_p.add_argument("--start",    "-s", type=str, help="From date  YYYY-MM-DD")
    view_p.add_argument("--end",      "-e", type=str, help="Until date YYYY-MM-DD")
    view_p.set_defaults(func=cmd_view)

    # ── delete ───────────────────────────────────────────────────────────
    del_p = sub.add_parser("delete", help="Delete an expense by ID")
    del_p.add_argument("id", type=int, help="Expense ID")
    del_p.set_defaults(func=cmd_delete)

    # ── summary ──────────────────────────────────────────────────────────
    sum_p = sub.add_parser("summary", help="Category breakdown + total")
    sum_p.add_argument("--start", "-s", type=str, help="From date  YYYY-MM-DD")
    sum_p.add_argument("--end",   "-e", type=str, help="Until date YYYY-MM-DD")
    sum_p.set_defaults(func=cmd_summary)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
