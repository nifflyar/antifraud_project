from dataclasses import dataclass


@dataclass
class CursorPaginationParams:
    """Parameters for cursor-based pagination."""

    cursor: str | None = None
    limit: int = 50
    sort_by: str = "id"
    sort_order: str = "desc"


@dataclass
class CursorPaginationResult:
    """Result of cursor-based pagination."""

    next_cursor: str | None
    prev_cursor: str | None
    has_more: bool
