from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class OverrideKind(str, Enum):
    SET_SHIFT = "set_shift"
    DAY_OFF = "day_off"
    VACATION = "vacation"
    SICK = "sick"


NON_WORKING_CODES = {"P", "VAC", "SICK", "OFF"}
WORKING_CODES = {"D", "V", "N"}


@dataclass(frozen=True)
class ManualOverride:
    employee: str
    date: int
    shift_code: str
    kind: OverrideKind
    locked: bool = True


def index_overrides(overrides: List[ManualOverride]):
    result: Dict[int, Dict[str, ManualOverride]] = {}
    for o in overrides:
        result.setdefault(o.date, {})[o.employee] = o
    return result


def get_override(lookup, day, employee):
    return lookup.get(day, {}).get(employee)
