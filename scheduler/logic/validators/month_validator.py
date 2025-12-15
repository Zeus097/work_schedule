from typing import Dict, List

SHIFT_WORK = {"Д", "В", "Н"}
SHIFT_ADMIN = "А"


def validate_month(schedule: Dict[str, Dict[int, str]]) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    days = sorted(next(iter(schedule.values())).keys())

    # -------- дневно покритие --------
    for day in days:
        used = []

        for _, data in schedule.items():
            code = data.get(day)
            if code in SHIFT_WORK:
                used.append(code)

        for req in SHIFT_WORK:
            if req not in used:
                errors.append(f"Ден {day}: липсва смяна {req}")

        if len(used) != len(set(used)):
            errors.append(f"Ден {day}: двойна смяна")

    return {
        "errors": errors,
        "warnings": warnings,
    }
