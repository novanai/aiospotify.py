from __future__ import annotations

import pydantic


@pydantic.dataclasses.dataclass
class APIError(Exception):
    """An API error."""

    status: int
    """The HTTP status code."""
    message: str | None
    """An error message, if provided."""

    def __str__(self) -> str:
        return f"Status: {self.status}. Message: {self.message}"
