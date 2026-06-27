class Expense:
    """
    Represents a single financial expense entry.

    Attributes:
        title (str): Short description of the expense.
        amount (float): Cost in rupees (must be > 0).
        category (str): Category tag e.g. 'food', 'rent', 'travel'.

    Example:
        >>> e = Expense("Coffee", 150, "food")
        >>> e.to_dict()
        {'title': 'Coffee', 'amount': 150, 'category': 'food'}
    """

    def __init__(self, title: str, amount: float, category: str):
        """
        Initialize an Expense.

        Args:
            title (str): Name of the expense.
            amount (float): Amount spent (must be positive).
            category (str): Category of spending.

        Raises:
            ValueError: If amount is zero or negative.
        """
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        self.title = title
        self.amount = amount
        self.category = category

    def to_dict(self) -> dict:
        """Convert expense to dictionary format for JSON storage."""
        return {"title": self.title, "amount": self.amount, "category": self.category}

    def __repr__(self) -> str:
        return f"Expense('{self.title}', ₹{self.amount}, '{self.category}')"