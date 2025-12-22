from __future__ import annotations

import calendar
from collections import deque

from scheduler.models import Employee, AdminEmployee
from scheduler.api.utils.holidays import get_holidays_for_month
from scheduler.logic.cycle_state import load_last_cycle_state

CYR = {"D": "Д", "V": "В", "N": "Н", "A": "А", "O": ""}


CYCLE = (
    ["N"] * 4 + ["O", "O"] +
    ["V"] * 4 + ["O"] +
    ["D"] * 4 + ["O"]
)
CYCLE_LEN = len(CYCLE)


def _init_stack(start_index: int) -> deque:
    d = deque(CYCLE)
    d.rotate(-start_index)
    return d


def generate_new_month(year: int, month: int) -> dict:
    _, days_in_month = calendar.monthrange(year, month)
    holidays = set(get_holidays_for_month(year, month))


    admin_qs = AdminEmployee.objects.select_related("employee").first()
    if not admin_qs:
        raise RuntimeError("Няма зададен администратор.")

    admin_id = str(admin_qs.employee.id)


    employees = {
        str(e["id"]): e["full_name"]
        for e in Employee.objects.filter(is_active=True)
        .values("id", "full_name")
    }

    if admin_id not in employees:
        raise RuntimeError("Администраторът не е активен служител.")

    rotational_ids = [eid for eid in employees if eid != admin_id]

    if len(rotational_ids) < 4:
        raise RuntimeError("Нужни са минимум 4 ротационни + 1 администратор.")


    cycle_state = load_last_cycle_state() or {}
    bootstrap = not cycle_state

    stacks = {}
    for emp_id in rotational_ids:
        if emp_id in cycle_state:
            start_index = int(cycle_state[emp_id]["cycle_index"])
        else:
            start_index = 0

        stacks[emp_id] = _init_stack(start_index)


    schedule = {
        emp_id: {d: "" for d in range(1, days_in_month + 1)}
        for emp_id in rotational_ids + [admin_id]
    }


    for day in range(1, days_in_month + 1):
        if calendar.weekday(year, month, day) < 5 and day not in holidays:
            schedule[admin_id][day] = "А"


    for day in range(1, days_in_month + 1):
        required = ["D", "V", "N"]
        used_today = {admin_id} if schedule[admin_id][day] == "А" else set()

        for shift in required:
            assigned = False

            for emp_id in rotational_ids:
                if emp_id in used_today:
                    continue

                stack = stacks[emp_id]

                for _ in range(CYCLE_LEN):
                    code = stack[0]
                    stack.rotate(-1)

                    if code == shift:
                        schedule[emp_id][day] = CYR[code]
                        used_today.add(emp_id)
                        assigned = True
                        break

                if assigned:
                    break

            if not assigned:
                raise RuntimeError(f"Невъзможно покритие за {shift} на ден {day}")

    return {
        "year": year,
        "month": month,
        "schedule": schedule,
        "overrides": {},
        "generator_locked": True,
    }
