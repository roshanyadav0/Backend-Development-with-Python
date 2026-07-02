from __future__ import annotations
import argparse
import sys
from datetime import date
from .tracker import ExpenseTracker
from .display import print_table, print_success, print_error, print_summary


# ── Sub-command handlers ───────────────────────────────────────────────────────

def cmd_add(args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()

    # Parse optional date (defaults to today)
    expense_date: date | None = None
    if args.date:
        try:
            expense_date = date.fromisoformat(args.date)
        except ValueError:
            print_error(f"Invalid date '{args.date}'. Use YYYY-MM-DD format.")
            sys.exit(1)

    expense = tracker.add(
        name=args.name,
        amount=args.amount,
        category=args.category,
        expense_date=expense_date,
        note=args.note,
    )
    print_success(
        f"Added expense #{expense.id}: '{expense.name}' "
        f"₹{expense.amount:,.2f} [{expense.category}] on {expense.date}"
    )


def cmd_view(args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()
    expenses = tracker.all()

    # Optional filter by category
    if args.category:
        expenses = [e for e in expenses if e.category.lower() == args.category.lower()]

    print_table(expenses)


def cmd_delete(args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()
    if tracker.delete(args.id):
        print_success(f"Deleted expense #{args.id}")
    else:
        print_error(f"No expense found with ID {args.id}")
        sys.exit(1)


def cmd_summary(_args: argparse.Namespace) -> None:
    tracker = ExpenseTracker()
    print_summary(tracker.by_category(), tracker.total())


# ── Parser setup ──────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense",
        description="💰 CLI Expense Tracker — manage your expenses from the terminal",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── add ──────────────────────────────────────────────────────────────
    add_p = sub.add_parser("add", help="Add a new expense")
    add_p.add_argument("name",     type=str,   help="Expense name  e.g. 'Coffee'")
    add_p.add_argument("amount",   type=float, help="Amount in ₹   e.g. 3.50")
    add_p.add_argument("category", type=str,   help="Category       e.g. Food")
    add_p.add_argument("--date",   type=str,   help="Date YYYY-MM-DD (default: today)")
    add_p.add_argument("--note",   type=str,   help="Optional note")
    add_p.set_defaults(func=cmd_add)

    # ── view ─────────────────────────────────────────────────────────────
    view_p = sub.add_parser("view", help="View all expenses")
    view_p.add_argument(
        "--category", "-c", type=str, help="Filter by category"
    )
    view_p.set_defaults(func=cmd_view)

    # ── delete ───────────────────────────────────────────────────────────
    del_p = sub.add_parser("delete", help="Delete an expense by ID")
    del_p.add_argument("id", type=int, help="Expense ID to delete")
    del_p.set_defaults(func=cmd_delete)

    # ── summary ──────────────────────────────────────────────────────────
    sum_p = sub.add_parser("summary", help="Category breakdown + total")
    sum_p.set_defaults(func=cmd_summary)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
