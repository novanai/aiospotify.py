import datetime
import enum
import typing as t

from spotify import types


def process_dict(dict_: dict[str, t.Any]) -> dict[str, t.Any]:
    return {
        k: v.value if isinstance(v, enum.Enum) else v
        for k, v in dict_.items()
        if v is not types.MISSING
    }


def datetime_from_timestamp(time: str) -> datetime.datetime:
    date = time.split("-")
    if len(date) == 1:
        return datetime.datetime(int(date[0]), 1, 1)
    elif len(date) == 2:
        return datetime.datetime(int(date[0]), int(date[1]), 1)
    else:
        return datetime.datetime(int(date[0]), int(date[1]), int(date[2]))


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
