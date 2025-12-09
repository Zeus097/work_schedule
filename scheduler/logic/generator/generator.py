from __future__ import annotations

import calendar
from scheduler.logic.configuration_helpers import load_config
from scheduler.logic.months_logic import get_latest_month

from scheduler.logic.generator.data_model import EmployeeState
from scheduler.logic.generator.workday_count import count_working_days
from scheduler.logic.generator.state_prep import prepare_employee_states
from scheduler.logic.generator.limits import choose_employee_for_shift
from scheduler.logic.generator.apply_shift import apply_shift


from scheduler.logic.generator.overrides import (
    index_overrides,
    get_override,
    WORKING_CODES,
    NON_WORKING_CODES,
)


SOFT_WORKDAYS_DEVIATION = 1
HARD_WORKDAYS_DEVIATION = 2


# ======================================
# MAIN GENERATOR
# ======================================

def generate_new_month(year, month, overrides=None):
    config = load_config()

    latest = get_latest_month()
    last_month_data = latest[2] if latest else None

    _, num_days = calendar.monthrange(year, month)

    schedule = {
        emp["name"]: {day: "" for day in range(1, num_days + 1)}
        for emp in config["employees"]
    }

    admin_name = config["admin"]["name"]
    schedule[admin_name] = {day: "" for day in range(1, num_days + 1)}

    override_index = index_overrides(overrides or [])

    employee_states = prepare_employee_states(config, last_month_data)

    # -----------------------------
    # Workday and date info
    # -----------------------------
    holidays = set()

    working_days_in_month = count_working_days(year, month, holidays)
    soft_min = working_days_in_month - SOFT_WORKDAYS_DEVIATION
    soft_max = working_days_in_month + SOFT_WORKDAYS_DEVIATION
    hard_min = working_days_in_month - HARD_WORKDAYS_DEVIATION
    hard_max = working_days_in_month + HARD_WORKDAYS_DEVIATION

    weekdays = {
        day: calendar.weekday(year, month, day)
        for day in range(1, num_days + 1)
    }

    # -----------------------------
    # ADMINISTRATOR SHIFTS
    # -----------------------------
    for day in range(1, num_days + 1):
        wd = weekdays[day]
        st_admin = employee_states[admin_name]

        if wd < 5 and day not in holidays:
            schedule[admin_name][day] = "А"
            apply_shift(st_admin, "A", is_workday=True)
        else:
            schedule[admin_name][day] = ""
            apply_shift(st_admin, "REST", is_workday=False)

    ideal_for_day = {
        day: {"D": None, "V": None, "N": None}
        for day in range(1, num_days + 1)
    }

    # =======================================================
    # MAIN LOOP — APPLY OVERRIDES FIRST, THEN GENERATE SHIFTS
    # =======================================================
    for day in range(1, num_days + 1):

        used_today = set()
        wd = weekdays[day]
        is_workday = wd < 5 and day not in holidays

        # ============================================
        # STEP 1 — APPLY MANUAL OVERRIDES FOR THIS DAY
        # ============================================
        for name, st in employee_states.items():
            if name == admin_name:
                continue

            ov = get_override(override_index, day, name)
            if not ov:
                continue


            if ov.shift_code in WORKING_CODES:
                translated = {"D": "Д", "V": "В", "N": "Н"}[ov.shift_code]
                schedule[name][day] = translated
                apply_shift(st, ov.shift_code, is_workday=True)
                used_today.add(name)
                continue

            if ov.shift_code in NON_WORKING_CODES:
                schedule[name][day] = "П"   # visual symbol (adjust if needed)
                apply_shift(st, "REST", is_workday=False)
                used_today.add(name)
                continue

        # ====================================================
        # STEP 2 – NORMAL SHIFT ASSIGNMENT FOR REMAINING CELLS
        # ====================================================
        # First, list employees blocked by overrides (cannot be assigned)
        blocked = set()
        for name in employee_states:
            if name == admin_name:
                continue
            if get_override(override_index, day, name):
                blocked.add(name)

        for shift_code, cyr in (("D", "Д"), ("V", "В"), ("N", "Н")):

            emp = choose_employee_for_shift(
                states=employee_states,
                shift_code=shift_code,
                admin_name=admin_name,
                used_today=used_today.union(blocked),
                crisis_mode=False,
                soft_min=soft_min,
                soft_max=soft_max,
                hard_min=hard_min,
                hard_max=hard_max
            )

            # If no employee found → try crisis mode
            if emp is None:
                emp = choose_employee_for_shift(
                    states=employee_states,
                    shift_code=shift_code,
                    admin_name=admin_name,
                    used_today=used_today.union(blocked),
                    crisis_mode=True,
                    soft_min=soft_min,
                    soft_max=soft_max,
                    hard_min=hard_min,
                    hard_max=hard_max
                )

            ideal_for_day[day][shift_code] = emp

            if emp:
                schedule[emp][day] = cyr
                used_today.add(emp)
                apply_shift(employee_states[emp], shift_code, is_workday)

        # Increment days_since for employees without a shift
        for name, st in employee_states.items():
            if name == admin_name:
                continue
            if schedule[name][day] not in ("Д", "В", "Н"):
                st.days_since += 1

    # Return structure
    return {
        "schedule": schedule,
        "ideal": ideal_for_day,
        "states": {name: vars(st) for name, st in employee_states.items()},
    }



