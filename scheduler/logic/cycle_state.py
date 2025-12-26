import json

from scheduler.logic.file_paths import DATA_DIR
from scheduler.logic.json_help_functions import _save_json_with_lock

LAST_CYCLE_FILE = DATA_DIR / "last_cycle_state.json"


def is_first_run() -> bool:
    return not any(DATA_DIR.iterdir())


def save_last_cycle_state(final_state: dict, last_date):

    state = {}

    for emp_id, info in final_state.items():
        state[str(emp_id)] = {
            "last_shift": info["last_shift"],
            "last_day": info["last_day"],
            "last_date": last_date.isoformat(),
        }

    _save_json_with_lock(LAST_CYCLE_FILE, state)



def load_last_cycle_state() -> dict:
    if not LAST_CYCLE_FILE.exists():
        return {}

    with LAST_CYCLE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)
