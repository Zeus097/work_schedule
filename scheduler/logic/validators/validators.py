from __future__ import annotations
from typing import Dict, List, Tuple

from scheduler.logic.rules import (
    is_shift_allowed,
    is_rest_like,
    to_lat,
    ShiftCode,
)

SHIFT_WORK = {"Д", "В", "Н"}


def validate_admin_shift(weekday: int, shift_lat: ShiftCode) -> bool:
    if is_rest_like(shift_lat):
        return True
    return shift_lat == "A" and weekday in (0, 1, 2, 3, 4)


def validate_month(
    schedule: Dict[str, Dict[int, str]],
    crisis_mode: bool,
    weekdays: Dict[int, int],
) -> List[Tuple[str, int, str]]:

    errors: List[Tuple[str, int, str]] = []

    # === 1. Проверка по служител ===
    for employee, days in schedule.items():
        prev_shift: ShiftCode | None = None
        last_work_day: int | None = None

        for day_str, shift_str in sorted(days.items(), key=lambda x: int(x[0])):
            day = int(day_str)
            shift_lat: ShiftCode = to_lat(shift_str)

            days_since = 999 if last_work_day is None else day - last_work_day

            if employee.lower().startswith("адм"):
                if not validate_admin_shift(weekdays[day], shift_lat):
                    errors.append(
                        (employee, day, "Администраторът не може да работи в този ден")
                    )
                continue

            if is_rest_like(shift_lat):
                continue

            if not is_shift_allowed(prev_shift, days_since, shift_lat, crisis_mode):
                errors.append(
                    (employee, day, f"Невалидна ротация след {prev_shift}")
                )

            prev_shift = shift_lat
            last_work_day = day

    # === 2. ДНЕВНО ПОКРИТИЕ ===
    days = next(iter(schedule.values())).keys()

    for day in days:
        counts = {"Д": 0, "В": 0, "Н": 0}

        for emp_days in schedule.values():
            shift = emp_days.get(day, "")
            if shift in counts:
                counts[shift] += 1

        for shift, cnt in counts.items():
            if cnt != 1:
                errors.append(
                    ("ПОКРИТИЕ", int(day), f"Смяна {shift} е {cnt} пъти (трябва 1)")
                )

    return errors
