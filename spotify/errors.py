from __future__ import annotations

import typing

import attrs


@attrs.frozen
class APIError(Exception):
    status: int
    message: str

    def __str__(self) -> str:
        return f"Status: {self.status}. Message: {self.message}"

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> APIError:
        return cls(
            payload["status"],
            payload["message"],
        )
