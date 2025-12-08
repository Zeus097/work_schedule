from __future__ import annotations

import calendar
from scheduler.logic.configuration_helpers import load_config
from scheduler.logic.months_logic import get_latest_month

from scheduler.logic.generator.data_model import EmployeeState
from scheduler.logic.generator.workday_count import count_working_days
from scheduler.logic.generator.state_prep import prepare_employee_states
from scheduler.logic.generator.limits import choose_employee_for_shift
from scheduler.logic.generator.apply_shift import apply_shift


SOFT_WORKDAYS_DEVIATION = 1
HARD_WORKDAYS_DEVIATION = 2


# ======================================
# MAIN GENERATOR
# ======================================

def generate_new_month(year, month):
    # -----------------------------
    # Load config and previous month state
    # -----------------------------
    config = load_config()

    latest = get_latest_month()
    last_month_data = latest[2] if latest else None

    _, num_days = calendar.monthrange(year, month)

    # -----------------------------
    # Initialize output schedule
    # -----------------------------
    schedule = {
        emp["name"]: {day: "" for day in range(1, num_days + 1)}
        for emp in config["employees"]
    }

    admin_name = config["admin"]["name"]
    schedule[admin_name] = {day: "" for day in range(1, num_days + 1)}

    # -----------------------------
    # Load employee states
    # -----------------------------
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
            # Workday → Admin works
            schedule[admin_name][day] = "А"
            apply_shift(st_admin, "A", is_workday=True)
        else:
            # Weekend/holiday → Admin rests
            schedule[admin_name][day] = ""
            apply_shift(st_admin, "REST", is_workday=False)

    ideal_for_day = {
        day: {"D": None, "V": None, "N": None}
        for day in range(1, num_days + 1)
    }

    # -----------------------------
    # MAIN LOOP — ASSIGN SHIFTS
    # -----------------------------
    for day in range(1, num_days + 1):
        used_today = set()
        wd = weekdays[day]
        is_workday = wd < 5 and day not in holidays

        for shift_code, cyr in (("D", "Д"), ("V", "В"), ("N", "Н")):

            emp = choose_employee_for_shift(
                states=employee_states,
                shift_code=shift_code,
                admin_name=admin_name,
                used_today=used_today,
                crisis_mode=False,
                soft_min=soft_min, soft_max=soft_max,
                hard_min=hard_min, hard_max=hard_max
            )

            # If no employee found → try crisis mode
            if emp is None:
                emp = choose_employee_for_shift(
                    states=employee_states,
                    shift_code=shift_code,
                    admin_name=admin_name,
                    used_today=used_today,
                    crisis_mode=True,
                    soft_min=soft_min, soft_max=soft_max,
                    hard_min=hard_min, hard_max=hard_max
                )

            ideal_for_day[day][shift_code] = emp

            if emp:
                schedule[emp][day] = cyr
                used_today.add(emp)
                apply_shift(employee_states[emp], shift_code, is_workday)

        for name, st in employee_states.items():
            if name == admin_name:
                continue
            if schedule[name][day] not in ("Д", "В", "Н"):
                st.days_since += 1

    return {
        "schedule": schedule,
        "ideal": ideal_for_day,
        "states": {name: vars(st) for name, st in employee_states.items()},
    }



