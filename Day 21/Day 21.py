# 1. Basic Annotations

# Variables
name: str = "Alice"
age: int = 30
price: float = 9.99
is_active: bool = True

# Built-in generics (3.9+, no need to import List/Dict anymore)
tags: list[str] = ["food", "rent"]
scores: dict[str, int] = {"math": 90, "sci": 85}
coords: tuple[int, int] = (10, 20)
unique_ids: set[int] = {1, 2, 3}

# Function parameters
def greet(name: str, age: int) -> str:
    return f"{name} is {age}"


# 2. Optional, Union — Old vs New (PEP 604, 3.10+)

# ── OLD WAY (pre-3.10) ──
from typing import Optional, Union

def find_user(user_id: int) -> Optional[str]:   # str OR None
    ...

def parse(value: Union[int, str]) -> int:       # int OR str
    ...


# ── NEW WAY (3.10+, PEP 604) ──
def find_user(user_id: int) -> str | None:      # cleaner!
    ...

def parse(value: int | str) -> int:
    ...

# Multiple unions
def process(data: int | float | str) -> bool:
    ...

# Optional list
def get_tags(item_id: int) -> list[str] | None:
    ...


# 3. Return Type Annotations

def add(a: int, b: int) -> int:
    return a + b

def get_name() -> str:
    return "Alice"

def log_message(msg: str) -> None:    # -> None means "returns nothing"
    print(msg)

def maybe_get_price(name: str) -> float | None:
    if name == "apple":
        return 1.5
    return None

# Returning multiple values (tuple)
def get_min_max(nums: list[int]) -> tuple[int, int]:
    return min(nums), max(nums)