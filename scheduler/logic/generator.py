from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional
from scheduler.logic.rules import (
    to_lat,
    is_working_shift,
    get_preferred_next_shift,
    is_shift_allowed,
)
from scheduler.logic.configuration_helpers import load_config
from scheduler.logic.months_logic import get_latest_month


MAX_CONSECUTIVE_SAME_SHIFT = 4
ADMIN_MAX_CONSECUTIVE_SAME_SHIFT = 5

SOFT_WORKDAYS_DEVIATION = 1
HARD_WORKDAYS_DEVIATION = 2


# ============================
#  DATA MODEL
# ============================

@dataclass
class EmployeeState:
    name: str
    last_shift: Optional[str]
    last_day: Optional[int]
    total_workdays: int
    days_since: int
    next_shift_ideal: Optional[str]
    consecutive_same_shift: int = 0


# ============================
#  WORKDAY COUNTING
# ============================

def count_working_days(year: int, month: int, holidays: set[date] | None = None) -> int:
    if holidays is None:
        holidays = set()

    _, days_in_month = calendar.monthrange(year, month)
    working_days = 0

    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        if d.weekday() < 5 and d not in holidays:
            working_days += 1

    return working_days


# ============================
#  STATE PREPARATION
# ============================

def prepare_employee_states(config, last_month_data) -> Dict[str, EmployeeState]:
    states: Dict[str, EmployeeState] = {}

    for emp in config["employees"]:
        name = emp["name"]
        last_shift_raw = emp.get("last_shift")
        last_shift = to_lat(last_shift_raw) if last_shift_raw else None

        states[name] = EmployeeState(
            name=name,
            last_shift=last_shift,
            last_day=None,
            total_workdays=0,
            days_since=999,
            next_shift_ideal=get_preferred_next_shift(last_shift) if last_shift else None,
            consecutive_same_shift=1 if last_shift in {"D", "V", "N"} else 0
        )

    admin_name = config["admin"]["name"]
    states[admin_name] = EmployeeState(
        name=admin_name,
        last_shift="A",
        last_day=None,
        total_workdays=0,
        days_since=999,
        next_shift_ideal="A",
        consecutive_same_shift=1
    )

    # Load real last shifts from previous month
    if last_month_data:
        for emp_name, month_days in last_month_data["days"].items():
            if emp_name not in states:
                continue

            last_cons = 0
            last_shift = None

            for day in sorted(month_days):
                shift_lat = to_lat(month_days[day])

                if is_working_shift(shift_lat):
                    last_shift = shift_lat
                    states[emp_name].last_day = day

                    if shift_lat == last_shift:
                        last_cons += 1
                    else:
                        last_cons = 1

            if last_shift:
                states[emp_name].last_shift = last_shift
                states[emp_name].consecutive_same_shift = last_cons

    # If last day exists → days_since = 1
    for st in states.values():
        if st.last_day is not None:
            st.days_since = 1

    return states


# ============================
#  LIMIT CHECKS
# ============================

def is_consecutive_allowed(state: EmployeeState, new_shift: str, is_admin: bool) -> bool:
    if new_shift not in {"D", "V", "N"}:
        return True

    if state.last_shift == new_shift:
        next_cons = state.consecutive_same_shift + 1
    else:
        next_cons = 1

    limit = ADMIN_MAX_CONSECUTIVE_SAME_SHIFT if is_admin else MAX_CONSECUTIVE_SAME_SHIFT
    return next_cons <= limit


def is_within_workday_limits(state: EmployeeState, is_admin: bool,
                             soft_min: int, soft_max: int,
                             hard_min: int, hard_max: int,
                             crisis_mode: bool) -> bool:

    # First month / no history
    if state.last_shift is None:
        return True

    if is_admin:
        return True

    days = state.total_workdays

    if days > hard_max:
        return False

    if days > soft_max and not crisis_mode:
        return False


    return True


def choose_employee_for_shift(
    states: Dict[str, EmployeeState],
    shift_code: str,
    admin_name: str,
    used_today: set,
    crisis_mode: bool,
    soft_min: int, soft_max: int, hard_min: int, hard_max: int
):
    candidates = []

    for name, st in states.items():
        is_admin = (name == admin_name)

        if is_admin:
            continue

        if name in used_today:
            continue

        # Rule: forbid V -> N
        if st.last_shift == "V" and shift_code == "N":
            continue

        # Rule: normal rotation rules
        if not is_shift_allowed(st.last_shift, st.days_since, shift_code, crisis_mode):
            continue

        # Rule: consecutive limits
        if not is_consecutive_allowed(st, shift_code, is_admin):
            continue

        # Rule: workday balance
        if not is_within_workday_limits(st, is_admin, soft_min, soft_max, hard_min, hard_max, crisis_mode):
            continue

        # Scoring: lower workdays first, more days_since first, matching ideal
        ideal_match = 1 if st.next_shift_ideal == shift_code else 0

        candidates.append((
            name,
            -ideal_match,
            -st.days_since,
            st.total_workdays
        ))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[1], x[2], x[3], x[0]))
    return candidates[0][0]


# ============================
#  APPLY SHIFT TO STATE
# ============================

def apply_shift(state: EmployeeState, shift_code: str, is_workday: bool):

    # --- WORKING SHIFTS (D/V/N/A) ---
    if shift_code in {"D", "V", "N", "A"}:

        # Consecutive rules
        if state.last_shift == shift_code:
            state.consecutive_same_shift += 1
        else:
            state.consecutive_same_shift = 1

        # Workday counting
        if is_workday:
            state.total_workdays += 1

        # Basic updates
        state.days_since = 0
        state.last_shift = shift_code

        # Ideal next shift
        from scheduler.logic.rules import get_preferred_next_shift
        state.next_shift_ideal = get_preferred_next_shift(shift_code)

    else:
        # --- REST / O ---
        state.consecutive_same_shift = 0
        state.days_since += 1
        state.last_shift = shift_code


# ============================
#  MAIN GENERATOR
# ============================

def generate_new_month(year, month):
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

    employee_states = prepare_employee_states(config, last_month_data)

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

    # ADMIN SHIFTS
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

    # MAIN LOOP
    for day in range(1, num_days + 1):
        used_today = set()
        wd = weekdays[day]
        is_workday = wd < 5 and day not in holidays

        for shift_code, cyr in (("D", "Д"), ("V", "В"), ("N", "Н")):
            emp = choose_employee_for_shift(
                employee_states,
                shift_code,
                admin_name,
                used_today,
                crisis_mode=False,
                soft_min=soft_min, soft_max=soft_max,
                hard_min=hard_min, hard_max=hard_max
            )

            if emp is None:
                emp = choose_employee_for_shift(
                    employee_states,
                    shift_code,
                    admin_name,
                    used_today,
                    crisis_mode=True,
                    soft_min=soft_min, soft_max=soft_max,
                    hard_min=hard_min, hard_max=hard_max
                )

            ideal_for_day[day][shift_code] = emp

            if emp:
                schedule[emp][day] = cyr
                used_today.add(emp)
                apply_shift(employee_states[emp], shift_code, is_workday)
            else:
                pass  # графикът ще остави тази смяна празна, ако никой не може

        # Everyone else gets days_since++
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
