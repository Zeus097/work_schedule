from __future__ import annotations

from typing import Dict, Optional, List, Tuple

from scheduler.logic.rules import (
    is_shift_allowed,
    is_rest_like,
    is_working_shift,
    to_lat,
    ShiftCode,
    TRANSITION_RULES
)


def validate_shift(prev_shift, days_since_last_work, new_shift, crisis_mode) -> bool:
    """
    Checks whether a current employee can work in this shift.
    """
    return is_shift_allowed(prev_shift, days_since_last_work, new_shift, crisis_mode)


def validate_admin_shift(weekday, new_shift) -> bool:
    """
    The Admin can work only from Monday to Friday (weekdays)
    If the shift is 'REST' or "VACANT DAY" - its always ok.
    """

    if is_rest_like(new_shift):
        return True


    # If not 'REST/О' -> 'А'
    if new_shift != "A":
        return False

    # A -> MONDAY – FRIDAY
    return weekday in (0, 1, 2, 3, 4)


def validate_month(schedule, crisis_mode, weekdays) -> List[Tuple[str, int, str]]:
    """
    Checks the entire monts.
    """

    errors = []

    # For every employee, checks the shift sequence.
    for employee, days in schedule.items():
        prev_shift_lat = None
        last_work_day = None

        for day, shift_str in days.items():
            shift_lat: ShiftCode = to_lat(shift_str)

            if last_work_day is None:
                days_since = 999  # 'days_since >= required_rest_days' will always be TRUE
            else:
                days_since = day - last_work_day

            if employee.lower().startswith("адм"):
                if not validate_admin_shift(weekdays[day], shift_lat):
                    errors.append((employee, day, "Администраторът не може да работи в този ден"))
                    continue

            if is_rest_like(shift_lat):
                continue

            if not validate_shift(prev_shift_lat, days_since, shift_lat, crisis_mode):
                errors.append((employee, day, f"Невалидна ротация след {prev_shift_lat}"))


            # Renew the last shift
            prev_shift_lat = shift_lat
            last_work_day = day

    return errors




