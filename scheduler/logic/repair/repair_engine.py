import calendar
from typing import Dict, List, Optional

SHIFT_WORK = {"Д", "В", "Н"}
SHIFT_ADMIN = "А"
BLOCKED = {"O", "B"}


def _day_int(day) -> int:
    return int(day)


def find_missing_shifts(schedule: Dict[str, Dict[str, str]], year, month, holidays: set[int],) -> Dict[int, List[str]]:
    """
        Identifies missing required shifts for each day in the month.
        Checks daily work shifts and admin coverage, accounting for weekends
        and holidays, and returns a mapping of day to missing shift codes.
    """

    missing = {}

    days = sorted(
        int(d) for d in next(iter(schedule.values())).keys()
    )

    for day in days:
        used = set()

        for data in schedule.values():
            if data.get(str(day)) in SHIFT_WORK:
                used.add(data[str(day)])

        need = [s for s in SHIFT_WORK if s not in used]

        if calendar.weekday(year, month, day) < 5 and day not in holidays:
            if SHIFT_ADMIN not in {
                data.get(str(day)) for data in schedule.values()
            }:
                need.append(SHIFT_ADMIN)

        if need:
            missing[day] = need

    return missing


def find_replacement(schedule: Dict[str, Dict[str, str]], day, shift, admins: set[str],) -> Optional[str]:
    """
        Finds a suitable employee to cover a missing shift on a given day.
        Selects the first available employee with no assigned shift,
        respects admin-only constraints, and skips blocked assignments.
    """

    d = str(day)
    for name, days in schedule.items():
        if days.get(d) != "":
            continue
        if shift == SHIFT_ADMIN and name not in admins:
            continue
        if days.get(d) in BLOCKED:
            continue
        return name

    return None


def apply_repair(schedule, year, month, holidays: set[int], admins: set[str],) -> Dict[str, Dict[str, str]]:
    """
        Attempts to repair a schedule by filling missing shifts.
        Creates a copy of the schedule, detects missing daily shifts,
        and assigns available employees to cover gaps where possible.
    """

    new_schedule = {
        name: days.copy() for name, days in schedule.items()
    }

    missing = find_missing_shifts(
        new_schedule, year, month, holidays
    )

    for day, shifts in missing.items():
        for shift in shifts:
            name = find_replacement(
                new_schedule, day, shift, admins
            )
            if name:
                new_schedule[name][str(day)] = shift

    return new_schedule
