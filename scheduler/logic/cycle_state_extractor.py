from datetime import date
from typing import Dict

from scheduler.logic.rules import to_lat, is_rest_like


def extract_cycle_state_from_schedule(
    schedule: Dict[str, Dict[str, str]],
    last_day: date,
    admin_id: str,
) -> Dict[str, dict]:
    """
        Извлича cycle_state от заключен месец.
        Връща САМО това, което генераторът реално използва.
    """

    state: Dict[str, dict] = {}

    last_day_num = last_day.day

    for emp_id, days in schedule.items():
        if emp_id == admin_id:
            continue

        last_shift = None
        last_work_day = None

        for d in range(last_day_num, 0, -1):
            shift = to_lat(days.get(str(d), ""))

            if is_rest_like(shift):
                continue

            last_shift = shift
            last_work_day = d
            break

        if last_shift is None:
            continue

        state[emp_id] = {
            "last_shift": last_shift,
            "last_day": last_work_day,
        }

    return state
