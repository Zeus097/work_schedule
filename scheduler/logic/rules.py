from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Optional


ShiftCode = Literal["D", "V", "N", "A", "O", "REST"]


TO_CYR = {
    "D": "Д",
    "V": "В",
    "N": "Н",
    "A": "А",
    "O": "О",
    "REST": "",  # REST – rest day (empty in UI)
}

TO_LAT = {v: k for k, v in TO_CYR.items() if v != ""}

TO_LAT[""] = "REST"
TO_LAT[" "] = "REST"
TO_LAT["-"] = "REST"


def to_cyr(code):
    """
    latin -> cyrilic (for UI/JSON output).
    """

    if code is None:
        return ""

    return TO_CYR.get(code, "")


def to_lat(code):
    """
    Translate cyrilic -> latin (for internal logic).
    """

    if code is None:
        return "REST"

    return TO_LAT.get(code, "REST")



WORKING_SHIFTS = {"D", "V", "N", "A"}
REAL_WORK_SHIFTS = {"D", "V", "N"}      # "А" is not in the shifting process!
REST_LIKE = {"REST", "O"}


def is_working_shift(code) -> bool:
    return code in WORKING_SHIFTS


def is_real_shift(code) -> bool:
    return code in REAL_WORK_SHIFTS


def is_rest_like(code) -> bool:
    return (code is None) or (code in REST_LIKE)



# --------------------------------------
@dataclass(frozen=True)
class ShiftTransitionRule:
    min_rest_days: int
    preferred_rest_days: int
    default_next: Optional[ShiftCode]


TRANSITION_RULES: Dict[str, ShiftTransitionRule] = {
    "N": ShiftTransitionRule(min_rest_days=1, preferred_rest_days=2, default_next="V"),
    "V": ShiftTransitionRule(min_rest_days=1, preferred_rest_days=1, default_next="D"),
    "D": ShiftTransitionRule(min_rest_days=1, preferred_rest_days=1, default_next="N"),
    "A": ShiftTransitionRule(min_rest_days=0, preferred_rest_days=0, default_next="A"),
    "O": ShiftTransitionRule(min_rest_days=0, preferred_rest_days=0, default_next=None),
    "REST": ShiftTransitionRule(min_rest_days=0, preferred_rest_days=0, default_next=None),
}


def get_transition_rule(prev_shift):
    if prev_shift is None:
        return ShiftTransitionRule(0, 0, None)

    return TRANSITION_RULES.get(prev_shift, ShiftTransitionRule(0, 0, None))


def get_preferred_next_shift(prev_shift):
    return get_transition_rule(prev_shift).default_next


def is_shift_allowed(
    prev_shift: Optional[str],
    days_since_last_work: int,
    new_shift: Optional[str],
    crisis_mode: bool = False,
) -> bool:

    if is_rest_like(new_shift):
        return True

    if days_since_last_work == 0 and is_working_shift(prev_shift) and is_working_shift(new_shift):
        return False

    if prev_shift is None:
        return True

    rule = get_transition_rule(prev_shift)

    required_rest = rule.preferred_rest_days
    if crisis_mode:
        required_rest = rule.min_rest_days

    if days_since_last_work < required_rest and is_real_shift(new_shift):
        return False

    if days_since_last_work < 1 and is_real_shift(new_shift):
        return False

    return True



