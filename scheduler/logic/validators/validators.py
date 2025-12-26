from __future__ import annotations
from typing import Dict, List, Tuple

from scheduler.logic.rules import (
    is_shift_allowed,
    is_rest_like,
    to_lat,
    ShiftCode,
)



ERROR_BLOCKING = "blocking"
ERROR_SOFT = "soft"

ValidationError = Tuple[str, int, str, str]

DAYLINE_SHIFTS = {"Д", "А"}   # 08:00–16:00
EVENING_SHIFT = "В"
NIGHT_SHIFT = "Н"




def validate_admin_shift(weekday: int, shift_lat: ShiftCode) -> bool:
    if is_rest_like(shift_lat):
        return True
    return shift_lat == "A" and weekday in (0, 1, 2, 3, 4)


def validate_month(
    schedule: Dict[str, Dict[int, str]],
    crisis_mode: bool,
    weekdays: Dict[int, int],
    admin_id: str,
) -> List[ValidationError]:

    admin_id = str(admin_id)
    errors: List[ValidationError] = []

    # ──────────────
    # Rotations
    # ──────────────
    for employee, days in schedule.items():
        prev_shift: ShiftCode | None = None
        last_work_day: int | None = None

        for day_str, shift_str in sorted(days.items(), key=lambda x: int(x[0])):
            day = int(day_str)
            shift_lat: ShiftCode = to_lat(shift_str)

            days_since = 999 if last_work_day is None else day - last_work_day

            if employee == admin_id:
                if not validate_admin_shift(weekdays[day], shift_lat):
                    errors.append(
                        (employee, day,
                         "Администраторът не може да работи в този ден",
                         ERROR_SOFT)
                    )
                continue

            if is_rest_like(shift_lat):
                continue

            if not is_shift_allowed(prev_shift, days_since, shift_lat, crisis_mode):
                errors.append(
                    (employee, day,
                     f"Невалидна ротация след {prev_shift}",
                     ERROR_SOFT)
                )

            prev_shift = shift_lat
            last_work_day = day

    days = next(iter(schedule.values())).keys()

    for day_str in days:
        day = int(day_str)

        coverage = {
            "DAY": 0,
            "В": 0,
            "Н": 0,
        }

        for emp_id, emp_days in schedule.items():
            shift = emp_days.get(str(day), "")

            if shift in DAYLINE_SHIFTS:
                coverage["DAY"] += 1

            elif shift == EVENING_SHIFT:
                coverage["В"] += 1

            elif shift == NIGHT_SHIFT:
                coverage["Н"] += 1

        # ───── Validations ─────

        if coverage["DAY"] == 0:
            errors.append(
                ("ПОКРИТИЕ", day,
                 "Липсва дневна смяна (Д или А)",
                 ERROR_BLOCKING)
            )

        if coverage["В"] != 1:
            errors.append(
                ("ПОКРИТИЕ", day,
                 f"Вечерна смяна (В) = {coverage['В']}",
                 ERROR_BLOCKING)
            )

        if coverage["Н"] != 1:
            errors.append(
                ("ПОКРИТИЕ", day,
                 f"Нощна смяна (Н) = {coverage['Н']}",
                 ERROR_BLOCKING)
            )

    return errors
