from __future__ import annotations

import calendar
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from scheduler.logic.rules import (
    to_lat,
    to_cyr,
    is_real_shift,
    is_working_shift,
    get_preferred_next_shift,
    is_shift_allowed,
)
from scheduler.logic.validators import validate_month
from scheduler.logic.configuration_helpers import load_config
from scheduler.logic.months_logic import (
    get_latest_month,
    save_month,
    get_month_path
)
from scheduler.logic.json_help_functions import _load_json


# Следващата стъпка: API за празници
# TODO: add function load_holidays(year)


@dataclass
class EmployeeState:
    name: str
    last_shift: Optional[str]
    last_day: Optional[int]
    total_workdays: int


def generate_new_month(year, month) -> Dict[str, Dict[int, str]]:
    config = load_config()

    latest = get_latest_month()
    last_month_data = latest[2] if latest else None

    _, num_days = calendar.monthrange(year, month)

    schedule: Dict[str, Dict[int, str]] = {
        emp["name"]: {day: "" for day in range(1, num_days + 1)}
        for emp in config["employees"]
    }

    schedule[config["admin"]["name"]] = {day: "" for day in range(1, num_days + 1)}

    employee_states = prepare_employee_states(config, last_month_data)

    ideal_for_day = {
        day: {"D": None, "V": None, "N": None}
        for day in range(1, num_days + 1)
    }

    holidays = set()

    weekdays = {day: calendar.weekday(year, month, day)
                for day in range(1, num_days + 1)}

    admin_name = config["admin"]["name"]
    is_workday = {}
    for day in range(1, num_days + 1):
        wd = weekdays[day]
        if wd < 5 and day not in holidays:
            is_workday[day] = True
        else:
            is_workday[day] = False

    for day in range(1, num_days + 1):
        if is_workday[day]:
            schedule[admin_name][day] = "А"
            employee_states[admin_name].total_workdays += 1
        else:
            schedule[admin_name][day] = ""

    for day in range(1, num_days + 1):
        ideal_for_day[day]["D"] = choose_ideal_employee(employee_states, "D")
        ideal_for_day[day]["V"] = choose_ideal_employee(employee_states, "V")
        ideal_for_day[day]["N"] = choose_ideal_employee(employee_states, "N")

    return {
        "schedule": schedule,
        "ideal": ideal_for_day,
        "states": {name: vars(st) for name, st in employee_states.items()},
    }



def prepare_employee_states(config, last_month_data) -> Dict[str, EmployeeState]:
    """
    Creates an internal state for employees:
        - last shift (in latin)
        - last day from last month
        - reset working days
    """

    states = {}

    for emp in config["employees"]:
        name = emp["name"]
        last_shift = emp.get("last_shift")


        if last_shift:
            last_shift = to_lat(last_shift)

        states[name] = EmployeeState(
            name=name,
            last_shift=last_shift,
            last_day=None,
            total_workdays=0,
        )


    admin = config["admin"]
    states[admin["name"]] = EmployeeState(
        name=admin["name"],
        last_shift="A",
        last_day=None,
        total_workdays=0
    )


    if last_month_data:
        for emp_name, month_days in last_month_data["days"].items():
            for day in sorted(month_days):
                shift_cyr = month_days[day]
                shift_lat = to_lat(shift_cyr)
                if is_working_shift(shift_lat):
                    states[emp_name].last_shift = shift_lat
                    states[emp_name].last_day = day


    # (days_since_last_work)
    for emp in states.values():
        if emp.last_day is None:
            emp.days_since = 999
        else:
            emp.days_since = 1


    # the perfect next shift
    for emp in states.values():
        if emp.last_shift:
            emp.next_shift_ideal = get_preferred_next_shift(emp.last_shift)
        else:
            emp.next_shift_ideal = None



    return states


def choose_ideal_employee(employees, shift_code):
    """
    Chooses best employee for current shift according to:
        - идеална ротация
        - дни почивка
        - баланс на работа
    """
    candidates = []

    for emp in employees.values():
        if emp.last_shift == "A":
            continue

        ideal_match = 1 if emp.next_shift_ideal == shift_code else 0

        candidates.append((
            ideal_match,          # 1 = perfect rotation
            emp.days_since,       # more rest days --> better
            -emp.total_workdays,  # less work = better
            emp.name              # for stability
        ))

    # Starts by priority
    candidates.sort(reverse=True)

    return candidates[0][3] if candidates else None
