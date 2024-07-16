from __future__ import annotations

import pydantic


@pydantic.dataclasses.dataclass
class APIError(Exception):
    status: int
    message: str | None

    def __str__(self) -> str:
        return f"Status: {self.status}. Message: {self.message}"
