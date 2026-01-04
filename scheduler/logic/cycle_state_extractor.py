from typing import Dict
from scheduler.logic.rules import to_lat, is_rest_like



CYCLE = [
    "Д", "Д", "Д", "Д",
    "",
    "Н", "Н", "Н", "Н",
    "", "",
    "В", "В", "В", "В",
    ""
]

CYCLE_LEN = len(CYCLE)



def extract_cycle_state_from_schedule(schedule, last_day, admin_id):
    state = {}

    for emp_id, days in schedule.items():
        if emp_id == admin_id:
            continue

        last_work_day = None
        last_shift = None

        for day_str in sorted(days.keys(), key=int):
            shift = days[day_str]
            if shift in ("Д", "Н", "В"):
                last_work_day = int(day_str)
                last_shift = shift

        if last_shift is None:
            cycle_index = 0
        else:
            cycle_index = max(
                i for i, s in enumerate(CYCLE) if s == last_shift
            ) + 1

        state[str(emp_id)] = {
            "cycle_index": cycle_index % CYCLE_LEN
        }

    return state


