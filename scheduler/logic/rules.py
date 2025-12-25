from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Dict, Optional


# Shift codes (internal latin)
ShiftCode = Literal["D", "V", "N", "A", "O", "REST"]


# Mappings
TO_CYR = {
    "D": "Д",
    "V": "В",
    "N": "Н",
    "A": "А",
    "O": "П",
    "REST": "",
}

TO_LAT = {v: k for k, v in TO_CYR.items() if v != ""}
TO_LAT[""] = "REST"
TO_LAT[" "] = "REST"
TO_LAT["-"] = "REST"


def to_cyr(code):
    if code is None:
        return ""
    return TO_CYR.get(code, "")


def to_lat(code):
    if code is None:
        return "REST"
    return TO_LAT.get(code, "REST")


# Shift categories
WORKING_SHIFTS = {"D", "V", "N", "A"}
REAL_WORK_SHIFTS = {"D", "V", "N"}
REST_LIKE = {"REST", "O"}


def is_working_shift(code) -> bool:
    return code in WORKING_SHIFTS


def is_real_shift(code) -> bool:
    return code in REAL_WORK_SHIFTS


def is_rest_like(code) -> bool:
    return code in REST_LIKE or code is None


@dataclass(frozen=True)
class ShiftTransitionRule:
    min_rest_days: int
    preferred_rest_days: int
    default_next: Optional[ShiftCode]


TRANSITION_RULES: Dict[str, ShiftTransitionRule] = {
    "D": ShiftTransitionRule(0, 0, "V"),
    "V": ShiftTransitionRule(0, 0, "D"),
    "N": ShiftTransitionRule(1, 1, "V"),
    "A": ShiftTransitionRule(0, 0, "A"),
    "O": ShiftTransitionRule(0, 0, None),
    "REST": ShiftTransitionRule(0, 0, None),
}


def get_transition_rule(prev_shift):
    if prev_shift is None:
        return ShiftTransitionRule(0, 0, None)
    return TRANSITION_RULES.get(prev_shift, ShiftTransitionRule(0, 0, None))


def get_preferred_next_shift(prev_shift):
    return get_transition_rule(prev_shift).default_next


def is_shift_allowed(prev_shift, days_since_last_work, new_shift, crisis_mode) -> bool:
    """ Validation of allowed shift """

    if is_rest_like(new_shift):
        return True

    if prev_shift is None:
        return True

    if new_shift == "A":
        return True

    if prev_shift in {"D", "V"} and new_shift in {"D", "V"}:
        if prev_shift == new_shift:
            return False

    if new_shift == "N" and prev_shift in {"D", "V"}:
        return False

    if new_shift == "N":
        required = 1
        if crisis_mode:
            required = 1
        if days_since_last_work < required:
            return False
        if prev_shift == "N":
            return False

    if prev_shift == "N" and new_shift in {"D", "V"}:
        required = 1
        if crisis_mode:
            required = 1
        if days_since_last_work < required:
            return False

    return True



