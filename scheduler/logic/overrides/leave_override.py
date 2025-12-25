from typing import Dict


LEAVE_CODES = {"O", "B"}


def apply_leave_overrides(schedule: Dict[str, Dict[int, str]], leaves: Dict[str, Dict[int, str]],):
    """
        Applies leave and sick-day overrides to an existing schedule.
        Returns a copied schedule where specified days are replaced
        with validated leave codes, without mutating the original data.
    """

    new_schedule = {}

    for name, days in schedule.items():
        new_schedule[name] = days.copy()

        if name not in leaves:
            continue

        for day, leave_code in leaves[name].items():
            if leave_code not in LEAVE_CODES:
                raise ValueError(
                    f"Невалиден код за отпуск/болничен: {leave_code}"
                )

            new_schedule[name][day] = leave_code

    return new_schedule
