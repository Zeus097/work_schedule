from __future__ import annotations

import calendar
from collections import deque
from typing import Dict

from scheduler.models import Employee, AdminEmployee
from scheduler.logic.cycle_state import load_last_cycle_state
from scheduler.api.utils.holidays import get_holidays_for_month


# ===============================
# 1️⃣ ЦИКЪЛ НА СМЕНИТЕ (ЧОВЕШКИ)
# ===============================

CYCLE = [
    "Д", "Д", "Д", "Д",
    "",
    "В", "В", "В", "В",
    "",
    "Н", "Н", "Н", "Н",
    "", ""
]

CYCLE_LEN = len(CYCLE)


def _build_cycle(start_index: int) -> deque:
    dq = deque(CYCLE)
    dq.rotate(-start_index)
    return dq


# ===============================
# 2️⃣ ГЕНЕРАТОР
# ===============================

def generate_new_month(year: int, month: int) -> dict:
    _, days_in_month = calendar.monthrange(year, month)
    holidays = set(get_holidays_for_month(year, month))

    # ---------- администратор ----------
    admin_rel = AdminEmployee.objects.select_related("employee").first()
    if not admin_rel:
        raise RuntimeError("Няма зададен администратор.")

    admin_id = str(admin_rel.employee.id)

    # ---------- служители ----------
    employees = {
        str(e["id"]): e["full_name"]
        for e in Employee.objects.filter(is_active=True)
        .values("id", "full_name")
    }

    if admin_id not in employees:
        raise RuntimeError("Администраторът не е активен служител.")

    workers = [eid for eid in employees if eid != admin_id]

    if len(workers) < 4:
        raise RuntimeError("Нужни са минимум 4 ротационни служители.")

    # ---------- cycle state ----------
    last_state = load_last_cycle_state() or {}

    cycles: Dict[str, deque] = {}
    for i, emp_id in enumerate(workers):
        start_index = last_state.get(emp_id, {}).get("cycle_index", i * 4)
        cycles[emp_id] = _build_cycle(start_index % CYCLE_LEN)

    # ---------- празен график ----------
    schedule = {
        emp_id: {day: "" for day in range(1, days_in_month + 1)}
        for emp_id in workers + [admin_id]
    }

    # ===============================
    # 3️⃣ ДЕН ПО ДЕН (БЛОКОВО)
    # ===============================

    for day in range(1, days_in_month + 1):
        weekday = calendar.weekday(year, month, day)

        # --- администратор ---
        if weekday < 5 and day not in holidays:
            schedule[admin_id][day] = "А"

        # --- служители ---
        today = {}

        for emp_id in workers:
            shift = cycles[emp_id][0]
            today.setdefault(shift, []).append(emp_id)

        # покритие
        required = {"Д", "В", "Н"}
        available = {k for k in today if k in required}

        if available != required:
            raise RuntimeError(
                f"Невъзможно покритие за ден {day}. "
                f"Покрито: {available}"
            )

        # точно 1 човек на смяна
        for shift in required:
            emp_id = today[shift].pop(0)
            schedule[emp_id][day] = shift

        # завъртаме циклите
        for emp_id in workers:
            cycles[emp_id].rotate(-1)

    return {
        "year": year,
        "month": month,
        "schedule": schedule,
        "overrides": {},
        "generator_locked": True,
    }
