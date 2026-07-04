from __future__ import annotations
import json
from pathlib import Path
from .models import Expense
from .exceptions import StorageError

DATA_FILE = Path("expenses.json")


def load(path: Path = DATA_FILE) -> list[Expense]:
    """
    Load expenses from JSON. Returns [] if the file doesn't exist yet.

    Raises:
        StorageError: if the file exists but cannot be read or is malformed.
    """
    if not path.exists():
        return []
    try:
        raw: list[dict[str, object]] = json.loads(path.read_text(encoding="utf-8"))
        return [Expense.from_dict(item) for item in raw]
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise StorageError(str(path), str(exc)) from exc


def save(expenses: list[Expense], path: Path = DATA_FILE) -> None:
    """
    Persist expenses to JSON (atomic write via temp file).

    Raises:
        StorageError: if the file cannot be written.
    """
    tmp = path.with_suffix(".tmp")
    try:
        payload = json.dumps([e.to_dict() for e in expenses], indent=2, ensure_ascii=False)
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(path)          # atomic on POSIX; best-effort on Windows
    except OSError as exc:
        tmp.unlink(missing_ok=True)
        raise StorageError(str(path), str(exc)) from exc
