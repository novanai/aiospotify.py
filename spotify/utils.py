import datetime
import enum
import typing as t

from spotify import types


def process_dict(dict_: dict[str, t.Any]) -> dict[str, t.Any]:
    return {
        k: v.value if isinstance(v, enum.Enum) else v for k, v in dict_.items() if v is not types.MISSING
    }


def datetime_from_timestamp(time: str) -> datetime.datetime:
    date = time.split("-")
    if len(date) == 1:
        return datetime.datetime(int(date[0]), 1, 1)
    elif len(date) == 2:
        return datetime.datetime(int(date[0]), int(date[1]), 1)
    else:
        return datetime.datetime(int(date[0]), int(date[1]), int(date[2]))
