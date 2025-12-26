from typing import Dict
from scheduler.logic.rules import to_lat, is_rest_like

def extract_cycle_state_from_schedule(
    schedule: Dict[str, Dict[str, str]],
    last_day,
    admin_id: str,
) -> Dict[str, dict]:

    state = {}

    for emp_id, days in schedule.items():
        last_shift = None
        last_work_day = None

        for day_str in sorted(days.keys(), key=int):
            shift = to_lat(days[day_str])

            if not shift or is_rest_like(shift):
                continue

            last_shift = shift
            last_work_day = int(day_str)

        if last_work_day is None:
            state[emp_id] = {
                "last_shift": None,
                "days_since": 999,
            }
        else:
            state[emp_id] = {
                "last_shift": last_shift,
                "days_since": (last_day.day - last_work_day),
            }

    return state
