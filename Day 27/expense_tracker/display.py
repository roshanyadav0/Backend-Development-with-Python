"""Terminal display helpers: tables, summaries, and coloured messages."""

from __future__ import annotations

from .models import Expense

# ANSI colour codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# Column name → display width
COLS: dict[str, int] = {
    "ID": 4,
    "Name": 22,
    "Amount": 12,
    "Category": 14,
    "Date": 12,
    "Note": 20,
}


def _row(*cells: str) -> str:
    """Format cells into a fixed-width table row."""
    widths = list(COLS.values())
    return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells))


def _sep() -> str:
    """Return a separator line matching column widths."""
    return "  ".join("-" * w for w in COLS.values())


def print_table(expenses: list[Expense]) -> None:
    """Print all expenses as a coloured, fixed-width table."""
    if not expenses:
        print(f"{YELLOW}  No expenses found.{RESET}")
        return
    print(f"\n{BOLD}{CYAN}{_row(*COLS.keys())}{RESET}")
    print(f"{CYAN}{_sep()}{RESET}")
    for expense in expenses:
        print(
            _row(
                str(expense.id),
                expense.name,
                expense.amount_str(),
                expense.category,
                str(expense.date),
                expense.note or "—",
            )
        )
    print(f"{CYAN}{_sep()}{RESET}")
    total = sum(e.amount for e in expenses)
    print(
        f"{BOLD}{GREEN}  {len(expenses)} expense(s)  |  Total: Rs.{total:,.2f}{RESET}\n"
    )


def print_summary(
    by_cat: dict[str, float],
    total: float,
    stats: dict[str, str] | None = None,
) -> None:
    """Print a category breakdown bar chart, and optional stats block."""
    print(f"\n{BOLD}{CYAN}  Category Breakdown{RESET}")
    print(f"{CYAN}  {'Category'.ljust(18)} {'Amount'.rjust(12)}  Chart{RESET}")
    print(f"{CYAN}  {'-' * 18} {'-' * 12}  {'-----'}{RESET}")
    max_amt = max(by_cat.values(), default=1)
    for cat, amt in by_cat.items():
        filled = int(amt / max_amt * 20)
        progress_bar = f"{YELLOW}{'█' * filled}{'░' * (20 - filled)}{RESET}"
        pct_label = f"{amt / total * 100:.1f}%"
        print(
            f"  {cat.ljust(18)} Rs.{amt:>9,.2f}  {progress_bar}  {DIM}{pct_label}{RESET}"
        )
    if stats:
        print(f"\n{BOLD}{CYAN}  Stats{RESET}")
        for label, value in stats.items():
            print(f"  {label.ljust(20)} {value}")
    print(f"\n{BOLD}{GREEN}  Grand Total: Rs.{total:,.2f}{RESET}\n")


def print_filter_header(
    category: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> None:
    """Print a dim header line showing active filter values."""
    parts: list[str] = []
    if category:
        parts.append(f"category={YELLOW}{category}{RESET}")
    if start:
        parts.append(f"from={YELLOW}{start}{RESET}")
    if end:
        parts.append(f"until={YELLOW}{end}{RESET}")
    print(f"\n{DIM}  Filtered by: {'  |  '.join(parts)}{RESET}")


def print_success(msg: str) -> None:
    """Print a green success message with a tick prefix."""
    print(f"{GREEN}✓  {msg}{RESET}")


def print_error(msg: str) -> None:
    """Print a red error message with a cross prefix."""
    print(f"{RED}✗  {msg}{RESET}")


def print_info(label: str, value: str) -> None:
    """Print a single cyan-labelled info line."""
    print(f"  {CYAN}{label.ljust(20)}{RESET} {value}")
