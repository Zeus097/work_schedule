from scheduler.logic.file_paths import DATA_DIR
from scheduler.logic.json_help_functions import (
    _load_json,
    _save_json_with_lock,
)
from scheduler.logic.months_logic import get_month_path



EMPLOYEES_FILE = DATA_DIR / "employees.json"


def create_empty_month(year, month):
    return {
        "schedule": {},
        "ideal": {},
        "states": {},
        "overrides": {}
    }


def load_employees() -> list[dict]:
    if not EMPLOYEES_FILE.exists():
        return []
    return _load_json(EMPLOYEES_FILE)


def save_employees(data: list[dict]) -> None:
    _save_json_with_lock(EMPLOYEES_FILE, data)


def clear_month_data(year: int, month: int) -> None:
    path = get_month_path(year, month)
    if path.exists():
        path.unlink()
