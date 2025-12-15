from __future__ import annotations
import calendar
from collections import deque

from scheduler.models import Employee, AdminEmployee
from scheduler.logic.file_paths import DATA_DIR
from scheduler.logic.json_help_functions import (
    _save_json_with_lock,
    load_cycle_state,
    save_cycle_state,
)
from scheduler.api.utils.holidays import get_holidays_for_month

CYR = {"D": "Д", "V": "В", "N": "Н", "A": "А", "O": ""}

# 🔁 ПРАВИЛЕН цикъл:
# 4N → 2O → 4V → 1O → 4D → 1O
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


def generate_new_month(year: int, month: int):
    _, days_in_month = calendar.monthrange(year, month)
    holidays = set(get_holidays_for_month(year, month))

    # -------- служители --------
    employees = list(
        Employee.objects.filter(is_active=True)
        .order_by("full_name")
        .values_list("full_name", flat=True)
    )

    admin_qs = AdminEmployee.objects.select_related("employee").first()
    admin = admin_qs.employee.full_name if admin_qs else None

    if not admin or len(employees) < 4:
        raise RuntimeError(
            "Невъзможно генериране: нужни са минимум 5 служителя "
            "(1 администратор + 4 ротационни)."
        )

    # -------- cycle state --------
    cycle_state = load_cycle_state()

    stacks = {}
    for name in employees:
        start_index = cycle_state.get(name, {}).get("cycle_index", 0)
        stacks[name] = _init_stack(start_index)

    # -------- график --------
    schedule = {
        name: {d: "" for d in range(1, days_in_month + 1)}
        for name in employees + [admin]
    }

    # -------- администратор --------
    for day in range(1, days_in_month + 1):
        if calendar.weekday(year, month, day) < 5 and day not in holidays:
            schedule[admin][day] = "А"

    # -------- основен цикъл --------
    for day in range(1, days_in_month + 1):
        required = ["D", "V", "N"]
        used_today = set()

        if schedule[admin][day] == "А":
            used_today.add(admin)

        for shift in required:
            assigned = False

            for name in employees:
                if name in used_today:
                    continue

                stack = stacks[name]

                for _ in range(CYCLE_LEN):
                    code = stack[0]
                    stack.rotate(-1)

                    if code == shift:
                        schedule[name][day] = CYR[code]
                        used_today.add(name)
                        assigned = True
                        break

                if assigned:
                    break

            if not assigned:
                raise RuntimeError(
                    f"Невъзможно покритие за {shift} на ден {day}"
                )

    # -------- save cycle state --------
    new_cycle_state = {}
    for name, stack in stacks.items():
        # колко позиции сме изминали от началото
        index = (-stack.index(CYCLE[0])) % CYCLE_LEN if CYCLE[0] in stack else 0
        new_cycle_state[name] = {
            "cycle_index": index,
            "last_date": f"{year}-{month:02d}-{days_in_month:02d}",
        }

    save_cycle_state(new_cycle_state)

    # -------- запис --------
    path = DATA_DIR / f"{year}-{month:02d}.json"
    _save_json_with_lock(path, {
        "year": year,
        "month": month,
        "schedule": schedule,
        "overrides": {},
        "generator_locked": True,
    })

    return {
        "schedule": schedule,
        "overrides": {},
        "generator_locked": True,
    }
