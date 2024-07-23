# Modified from https://github.com/hikari-py/hikari/blob/master/hikari/undefined.py

from __future__ import annotations
import typing

__all__: typing.Sequence[str] = (
    "MISSING",
    "MissingOr",
    "MissingType",
)

if typing.TYPE_CHECKING:
    from typing import Self


class MissingType:
    """The type of the [`MISSING`][spotify.types.MISSING] singleton sentinel value."""

    __slots__: typing.Sequence[str] = ()

    def __bool__(self) -> typing.Literal[False]:
        return False

    def __copy__(self) -> Self:
        # This is meant to be a singleton
        return self

    def __deepcopy__(self, memo: typing.MutableMapping[int, typing.Any]) -> Self:
        memo[id(self)] = self

        # This is meant to be a singleton
        return self

    def __getstate__(self) -> typing.Any:
        # Returning False tells pickle to not call `__setstate__` on unpickling.
        return False

    def __repr__(self) -> str:
        return "MISSING"

    def __reduce__(self) -> str:
        # Returning a string makes pickle fetch from the module namespace.
        return "MISSING"

    def __str__(self) -> str:
        return "MISSING"


MISSING = MissingType()
"""A sentinel singleton that denotes a missing or omitted value."""


def __new__(cls: MissingType) -> typing.NoReturn:
    raise TypeError("Cannot initialize multiple instances of singleton MISSING")


MissingType.__new__ = __new__  # pyright: ignore[reportAttributeAccessIssue]
del __new__

T = typing.TypeVar("T", covariant=True)
MissingOr = typing.Union[T, MissingType]
"""Type hint to mark a type as being semantically optional."""
