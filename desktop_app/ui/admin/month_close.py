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
        "employees": snapshot,
        "closed": True   # 🔒 ЯВЕН ФЛАГ
    }

    with open(LAST_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_month_closed(year: int, month: int) -> bool:
    """
    Проверява дали даден месец е заключен.
    """
    if not LAST_STATE_FILE.exists():
        return False

    try:
        with open(LAST_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False

    return (
        data.get("closed") is True
        and data.get("year") == year
        and data.get("month") == month
    )
