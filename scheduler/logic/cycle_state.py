from pathlib import Path
from scheduler.logic.file_paths import DATA_DIR
from scheduler.logic.json_help_functions import _save_json_with_lock

LAST_STATE_FILE = DATA_DIR / "last_cycle_state.json"


def save_last_cycle_state(schedule: dict, last_date):
    state = {}

    for name, days in schedule.items():
        # броим САМО реалните смени, не О/Б
        worked = [d for d in days.values() if d in {"Д", "В", "Н"}]

        state[name] = {
            "cycle_index": len(worked) % 14,  # според твоя цикъл
            "last_date": last_date.isoformat(),
        }

    _save_json_with_lock(LAST_STATE_FILE, state)



