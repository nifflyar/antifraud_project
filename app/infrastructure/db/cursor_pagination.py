import base64
import json
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class CursorPage(Generic[T]):
    """Cursor-based pagination response."""

    items: list[T]
    next_cursor: str | None
    prev_cursor: str | None
    has_more: bool
    total_count: int | None = None


def encode_cursor(primary_key: int | str, sort_value: Any) -> str:
    """Encode cursor as base64(pk, sort_value) for stable ordering."""
    data = {"pk": str(primary_key), "sv": str(sort_value) if sort_value is not None else ""}
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> tuple[str, str]:
    """Decode base64 cursor back to (primary_key, sort_value)."""
    try:
        data = json.loads(base64.b64decode(cursor.encode()).decode())
        return data["pk"], data["sv"]
    except (ValueError, KeyError, json.JSONDecodeError):
        raise ValueError(f"Invalid cursor: {cursor}")
