from __future__ import annotations
from typing import Dict

from scheduler.logic.rules import to_lat
from .data_model import EmployeeState


BLOCK_LENGTH = 4
REST_AFTER_N = 2
REST_BETWEEN_BLOCKS = 1


def _seed_shift(name: str) -> str:
    s = sum(ord(c) for c in name)
    return ("D", "V", "N")[s % 3]


def prepare_employee_states(config, last_month_data) -> Dict[str, EmployeeState]:
    states: Dict[str, EmployeeState] = {}

    for emp in config["employees"]:
        name = emp["name"]
        states[name] = EmployeeState(
            name=name,
            last_shift=None,
            last_day=None,
            total_workdays=0,
            days_since_work=999,
            worked_yesterday=False,
            current_block_shift=None,
            block_days_left=0,
            rest_days_left=0,
            seed_start_shift=_seed_shift(name),
        )

    admin = config["admin"]["name"]
    states[admin] = EmployeeState(
        name=admin,
        last_shift="A",
        last_day=None,
        total_workdays=0,
        days_since_work=999,
        worked_yesterday=False,
        current_block_shift=None,
        block_days_left=0,
        rest_days_left=0,
        seed_start_shift="D",
    )

    if not last_month_data or "days" not in last_month_data:
        return states

    for name, days in last_month_data["days"].items():
        if name not in states:
            continue

        st = states[name]
        last = None
        streak = 0

        for d in sorted(days, key=lambda x: int(x)):
            lat = to_lat(days[d])
            if lat in {"D", "V", "N", "A"}:
                if lat == last:
                    streak += 1
                else:
                    last = lat
                    streak = 1
                st.last_shift = lat
                st.last_day = int(d)

        if last in {"D", "V", "N"} and streak < BLOCK_LENGTH:
            st.current_block_shift = last
            st.block_days_left = BLOCK_LENGTH - streak
        elif last == "N":
            st.rest_days_left = REST_AFTER_N
        else:
            st.rest_days_left = REST_BETWEEN_BLOCKS

    return states
