# expense_tracker/utils.py

def format_currency(amount: float, symbol: str = "₹") -> str:
    return f"{symbol}{amount:,.2f}"

def validate_amount(amount) -> float:
    amount = float(amount)
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    return amount