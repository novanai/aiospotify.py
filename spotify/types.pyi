# Modified from https://github.com/hikari-py/hikari/blob/master/hikari/undefined.pyi

import enum as __enum
from typing import Literal as __Literal
from typing import TypeVar as __TypeVar
from typing import Union as __Union

class MissingType(__enum.Enum):
    def __bool__(self) -> __Literal[False]: ...
    MISSING = __enum.auto()

MISSING: __Literal[MissingType.MISSING] = MissingType.MISSING

__T = __TypeVar("__T", covariant=True)

MissingOr = __Union[__T, MissingType]
