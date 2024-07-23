from __future__ import annotations

import typing

import pydantic

__all__: typing.Sequence[str] = ("APIError", "InvalidPayloadError")


@pydantic.dataclasses.dataclass
class APIError(Exception):
    """An API error."""

    status: int
    """The HTTP status code."""
    message: str | None
    """An error message, if provided."""

    def __str__(self) -> str:
        return f"Status: {self.status}. Message: {self.message}"


class InvalidPayloadError(Exception):
    """Error raised when spotify sends an invalid JSON payload that cannot be decoded."""
