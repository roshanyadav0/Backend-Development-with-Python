from __future__ import annotations
from .models import Expense

# ANSI colours
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

COLS = {
    "ID":       4,
    "Name":    22,
    "Amount":   12,
    "Category": 14,
    "Date":     12,
    "Note":     20,
}


def _row(*cells: str) -> str:
    widths = list(COLS.values())
    parts = [str(c).ljust(widths[i]) for i, c in enumerate(cells)]
    return "  ".join(parts)


def _separator() -> str:
    return "  ".join("-" * w for w in COLS.values())


def print_filter_header(
    category: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> None:
    parts: list[str] = []
    if category:
        parts.append(f"category={YELLOW}{category}{RESET}")
    if start:
        parts.append(f"from={YELLOW}{start}{RESET}")
    if end:
        parts.append(f"until={YELLOW}{end}{RESET}")
    label = "  |  ".join(parts)
    print(f"\n{DIM}  Filtered by: {label}{RESET}")


def print_table(expenses: list[Expense]) -> None:
    if not expenses:
        print(f"{YELLOW}  No expenses found.{RESET}")
        return

    header = _row(*COLS.keys())
    print(f"\n{BOLD}{CYAN}{header}{RESET}")
    print(f"{CYAN}{_separator()}{RESET}")

    for e in expenses:
        row = _row(
            str(e.id),
            e.name,
            f"Rs.{e.amount:,.2f}",
            e.category,
            str(e.date),
            e.note or "—",
        )
        print(row)

    print(f"{CYAN}{_separator()}{RESET}")
    total = sum(e.amount for e in expenses)
    count = len(expenses)
    print(f"{BOLD}{GREEN}  {count} expense(s)  |  Total: Rs.{total:,.2f}{RESET}\n")


def print_summary(by_cat: dict[str, float], total: float) -> None:
    print(f"\n{BOLD}{CYAN}  Category Breakdown{RESET}")
    print(f"{CYAN}  {'Category'.ljust(18)} {'Amount'.rjust(12)}  Chart{RESET}")
    print(f"{CYAN}  {'-'*18} {'-'*12}  {'-----'}{RESET}")

    max_amt = max(by_cat.values(), default=1)
    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        pct  = int(amt / max_amt * 20)
        bar  = f"{YELLOW}{'█' * pct}{'░' * (20 - pct)}{RESET}"
        pct_label = f"{amt / total * 100:.1f}%"
        print(f"  {cat.ljust(18)} Rs.{amt:>9,.2f}  {bar}  {DIM}{pct_label}{RESET}")

    print(f"\n{BOLD}{GREEN}  Grand Total: Rs.{total:,.2f}{RESET}\n")


def print_success(msg: str) -> None:
    print(f"{GREEN}✓  {msg}{RESET}")


def print_error(msg: str) -> None:
    print(f"{RED}✗  {msg}{RESET}")
