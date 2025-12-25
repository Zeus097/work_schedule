import json
from pathlib import Path

from scheduler.logic.file_paths import DATA_DIR
from scheduler.logic.json_help_functions import _save_json_with_lock

LAST_CYCLE_FILE = DATA_DIR / "last_cycle_state.json"


def is_first_run() -> bool:
    return not any(DATA_DIR.iterdir())


def save_last_cycle_state(schedule: dict, last_date):
    """
        Persists the last cycle state for each employee.
        Calculates the next cycle index based on worked shifts
        and stores it together with the last processed date.
    """

    state = {}

    for name, days in schedule.items():
        worked = [d for d in days.values() if d in {"Д", "В", "Н"}]
        state[name] = {
            "cycle_index": len(worked) % 14,
            "last_date": last_date.isoformat(),
        }

    _save_json_with_lock(LAST_CYCLE_FILE, state)


def load_last_cycle_state() -> dict:
    if not LAST_CYCLE_FILE.exists():
        return {}

    with LAST_CYCLE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)
