from __future__ import annotations

import calendar
from dataclasses import dataclass
from typing import Dict, Optional
from scheduler.logic.rules import (
    to_lat,
    is_working_shift,
    get_preferred_next_shift,
    is_shift_allowed,
)
from scheduler.logic.configuration_helpers import load_config
from scheduler.logic.months_logic import get_latest_month



@dataclass
class EmployeeState:
    name: str
    last_shift: Optional[str]
    last_day: Optional[int]
    total_workdays: int
    days_since: int
    next_shift_ideal: Optional[str]


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
        )

    admin_name = config["admin"]["name"]
    states[admin_name] = EmployeeState(
        name=admin_name,
        last_shift="A",
        last_day=None,
        total_workdays=0,
        days_since=999,
        next_shift_ideal="A",
    )

    if last_month_data:
        for emp_name, month_days in last_month_data["days"].items():

            if emp_name not in states:
                continue

            for day in sorted(month_days):
                shift_lat = to_lat(month_days[day])

                if is_working_shift(shift_lat):
                    states[emp_name].last_shift = shift_lat
                    states[emp_name].last_day = day

    for st in states.values():

        if st.last_day is not None:
            st.days_since = 1

    return states


def choose_best_employee(
    states: Dict[str, EmployeeState],
    shift_code: str,
    admin_name: str,
    used_today: set,
    crisis_mode: bool,
):
    candidates = []
    for name, st in states.items():

        if name == admin_name:
            continue

        if name in used_today:
            continue

        if not is_shift_allowed(st.last_shift, st.days_since, shift_code, crisis_mode):
            continue

        ideal_match = 1 if st.next_shift_ideal == shift_code else 0
        candidates.append((name, ideal_match, st.days_since, st.total_workdays))

    if not candidates:
        return None

    def key(item):
        name, ideal_match, days_since, total_work = item
        return (-ideal_match, -days_since, total_work, name)

    candidates.sort(key=key)
    return candidates[0][0]


def generate_new_month(year, month):
    config = load_config()

    latest = get_latest_month()
    last_month_data = latest[2] if latest else None

    _, num_days = calendar.monthrange(year, month)

    schedule: Dict[str, Dict[int, str]] = {
        emp["name"]: {day: "" for day in range(1, num_days + 1)}
        for emp in config["employees"]
    }
    admin_name = config["admin"]["name"]
    schedule[admin_name] = {day: "" for day in range(1, num_days + 1)}

    employee_states = prepare_employee_states(config, last_month_data)

    holidays = set()

    weekdays = {
        day: calendar.weekday(year, month, day)
        for day in range(1, num_days + 1)
    }

    for day in range(1, num_days + 1):
        wd = weekdays[day]

        if wd < 5 and day not in holidays:
            schedule[admin_name][day] = "А"
            st_admin = employee_states[admin_name]
            st_admin.last_shift = "A"
            st_admin.days_since = 0
            st_admin.total_workdays += 1
        else:
            schedule[admin_name][day] = ""
            st_admin = employee_states[admin_name]
            st_admin.last_shift = "REST"
            st_admin.days_since += 1

    ideal_for_day: Dict[int, Dict[str, Optional[str]]] = {
        day: {"D": None, "V": None, "N": None}
        for day in range(1, num_days + 1)
    }

    for day in range(1, num_days + 1):
        used_today = set()

        for shift_code, cyr in (("D", "Д"), ("V", "В"), ("N", "Н")):
            emp_name = choose_best_employee(
                employee_states,
                shift_code,
                admin_name,
                used_today,
                crisis_mode=False,
            )

            if emp_name is None:
                emp_name = choose_best_employee(
                    employee_states,
                    shift_code,
                    admin_name,
                    used_today,
                    crisis_mode=True,
                )

            ideal_for_day[day][shift_code] = emp_name

            if emp_name:
                schedule[emp_name][day] = cyr
                used_today.add(emp_name)

        for name, st in employee_states.items():

            if name == admin_name:
                continue

            assigned_cyr = schedule[name][day]

            if assigned_cyr in ("Д", "В", "Н"):
                st.last_shift = to_lat(assigned_cyr)
                st.days_since = 0
                st.total_workdays += 1
                st.next_shift_ideal = get_preferred_next_shift(st.last_shift)
            else:
                st.days_since += 1

    return {
        "schedule": schedule,
        "ideal": ideal_for_day,
        "states": {name: vars(st) for name, st in employee_states.items()},
    }


