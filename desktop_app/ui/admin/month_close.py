import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[3] / "data"
LAST_STATE_FILE = DATA_DIR / "last_state.json"


def extract_last_shifts(schedule: dict, days_in_month: int) -> dict:
    """
    Взима ПОСЛЕДНАТА реална смяна за всеки служител,
    броейки от края на месеца назад.
    """
    result = {}

    for name, days in schedule.items():
        for day in range(days_in_month, 0, -1):
            shift = days.get(day)
            if shift and shift.strip():
                result[name] = shift
                break

    return result


def save_last_state(year: int, month: int, snapshot: dict):
    """
    Записва потвърдения last_state,
    който ще се ползва като вход за следващия месец.
    """
    DATA_DIR.mkdir(exist_ok=True)

    data = {
        "year": year,
        "month": month,
        "employees": snapshot
    }

    with open(LAST_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
