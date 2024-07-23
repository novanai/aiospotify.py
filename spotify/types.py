# Modified from https://github.com/hikari-py/hikari/blob/master/hikari/undefined.py

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Self

__all__: typing.Sequence[str] = (
    "MissingType",
    "MISSING",
    "MissingOr",
)


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


# MIT License
#
# Copyright (c) 2022-present novanai
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
