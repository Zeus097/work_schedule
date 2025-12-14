from __future__ import annotations
import calendar
from collections import deque

from scheduler.models import Employee, AdminEmployee
from scheduler.logic.file_paths import DATA_DIR
from scheduler.logic.json_help_functions import _save_json_with_lock
from scheduler.api.utils.holidays import get_holidays_for_month

CYR = {"D": "Д", "V": "В", "N": "Н", "A": "А", "O": ""}

# 🔁 Основен цикъл със 2 дни почивка след нощна
CYCLE = (
    ["D"] * 4 + ["O"] +
    ["V"] * 4 + ["O"] +
    ["N"] * 4 + ["O", "O"]
)

LAST_STATE_FILE = DATA_DIR / "last_state.json"


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

    # ❌ твърдо правило
    if not admin or len(employees) < 4:
        raise RuntimeError(
            "Невъзможно генериране: нужни са минимум 5 служителя "
            "(1 администратор + 4 ротационни)."
        )

    # -------- стек за всеки служител --------
    stacks = {
        name: deque(CYCLE)
        for name in employees
    }

    # -------- график --------
    schedule = {
        name: {d: "" for d in range(1, days_in_month + 1)}
        for name in employees + [admin]
    }

    # -------- администратор (само А, делници) --------
    for day in range(1, days_in_month + 1):
        if calendar.weekday(year, month, day) < 5 and day not in holidays:
            schedule[admin][day] = "А"

    # -------- основен цикъл --------
    for day in range(1, days_in_month + 1):
        wd = calendar.weekday(year, month, day)
        is_weekend = wd >= 5 or day in holidays

        required = ["D", "V", "N"]

        used_today = set()

        # админ не влиза в ротацията
        if schedule[admin][day] == "А":
            used_today.add(admin)

        for shift in required:
            assigned = False

            for name in employees:
                if name in used_today:
                    continue

                stack = stacks[name]

                # въртим докато намерим работна смяна
                for _ in range(len(stack)):
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





