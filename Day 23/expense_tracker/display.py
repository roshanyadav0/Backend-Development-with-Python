from __future__ import annotations
from .models import Expense

# ANSI colours
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

COLS = {
    "ID":       4,
    "Name":    22,
    "Amount":   9,
    "Category":14,
    "Date":    12,
    "Note":    20,
}


def _row(*cells: str) -> str:
    widths = list(COLS.values())
    parts = [str(c).ljust(widths[i]) for i, c in enumerate(cells)]
    return "  ".join(parts)


def _separator() -> str:
    return "  ".join("-" * w for w in COLS.values())


def print_table(expenses: list[Expense]) -> None:
    if not expenses:
        print(f"{YELLOW}No expenses found.{RESET}")
        return

    header = _row(*COLS.keys())
    print(f"\n{BOLD}{CYAN}{header}{RESET}")
    print(f"{CYAN}{_separator()}{RESET}")

    for e in expenses:
        row = _row(
            str(e.id),
            e.name,
            f"₹{e.amount:,.2f}",
            e.category,
            str(e.date),
            e.note or "—",
        )
        print(row)

    print(f"{CYAN}{_separator()}{RESET}")
    total = sum(e.amount for e in expenses)
    print(f"{BOLD}{GREEN}  Total: ₹{total:,.2f}{RESET}\n")


def print_success(msg: str) -> None:
    print(f"{GREEN}✓  {msg}{RESET}")


def print_error(msg: str) -> None:
    print(f"{RED}✗  {msg}{RESET}")


def print_summary(by_cat: dict[str, float], total: float) -> None:
    print(f"\n{BOLD}{CYAN}  Category Breakdown{RESET}")
    print(f"{CYAN}  {'Category'.ljust(18)} Amount{RESET}")
    print(f"{CYAN}  {'-'*18} {'------'}{RESET}")
    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        bar = "█" * min(int(amt / max(by_cat.values()) * 20), 20)
        print(f"  {cat.ljust(18)} ₹{amt:>10,.2f}  {YELLOW}{bar}{RESET}")
    print(f"\n{BOLD}{GREEN}  Grand Total: ₹{total:,.2f}{RESET}\n")
