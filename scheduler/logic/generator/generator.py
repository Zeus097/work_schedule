from __future__ import annotations

import calendar
from datetime import date
from typing import Dict

from scheduler.logic.cycle_state import load_last_cycle_state
from scheduler.api.utils.holidays import get_holidays_for_month
from scheduler.logic.months_logic import load_month


CYCLE = [
    "Д", "Д", "Д", "Д",
    "",
    "Н", "Н", "Н", "Н",
    "", "",
    "В", "В", "В", "В",
    ""
]
CYCLE_LEN = len(CYCLE)

REQUIRED_SHIFTS = ("Д", "В", "Н")


def generate_new_month(
    year: int,
    month: int,
    employees: Dict[str, str],
    strict: bool = True,
) -> dict:
    _, days_in_month = calendar.monthrange(year, month)
    holidays = set(get_holidays_for_month(year, month))

    data = load_month(year, month)
    admin_id = data.get("month_admin_id")

    if not admin_id:
        raise RuntimeError("Няма зададен администратор за месеца.")

    if admin_id not in employees:
        raise RuntimeError("Администраторът не е активен служител.")

    workers = [eid for eid in employees if eid != admin_id]

    if len(workers) < 4:
        raise RuntimeError("Нужни са минимум 4 ротационни служители.")

    last_state = load_last_cycle_state() or {}

    cycle_pos: Dict[str, int] = {}
    for i, emp_id in enumerate(workers):
        start = last_state.get(str(emp_id), {}).get("cycle_index")
        if start is None:
            start = i * 4
        cycle_pos[str(emp_id)] = int(start) % CYCLE_LEN

    schedule = {
        emp_id: {str(day): "" for day in range(1, days_in_month + 1)}
        for emp_id in workers + [admin_id]
    }

    for day in range(1, days_in_month + 1):
        weekday = calendar.weekday(year, month, day)

        if weekday < 5 and day not in holidays:
            schedule[admin_id][str(day)] = "А"

        candidates = {s: [] for s in REQUIRED_SHIFTS}

        for emp_id in workers:
            idx = cycle_pos[str(emp_id)]
            shift = CYCLE[idx]
            if shift in candidates:
                candidates[shift].append(emp_id)

        missing = [s for s in REQUIRED_SHIFTS if not candidates[s]]
        if missing:
            if strict:
                raise RuntimeError(
                    f"Невъзможно покритие за ден {day}. Липсват: {', '.join(missing)}"
                )
            for emp_id in workers:
                cycle_pos[str(emp_id)] = (cycle_pos[str(emp_id)] + 1) % CYCLE_LEN
            continue

        for s in REQUIRED_SHIFTS:
            emp_id = candidates[s][0]
            schedule[emp_id][str(day)] = s

        for emp_id in workers:
            cycle_pos[str(emp_id)] = (cycle_pos[str(emp_id)] + 1) % CYCLE_LEN

    return {
        "year": year,
        "month": month,
        "schedule": schedule,
        "overrides": {},
        "generator_locked": strict,
        "month_admin_id": admin_id,
    }
