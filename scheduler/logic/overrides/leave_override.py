from typing import Dict


LEAVE_CODES = {"O", "B"}  # отпуск, болничен


def apply_leave_overrides(
    schedule: Dict[str, Dict[int, str]],
    leaves: Dict[str, Dict[int, str]],
) -> Dict[str, Dict[int, str]]:
    """
    leaves пример:
    {
      "Емре Адемов Ибрямов": {
          10: "O",
          11: "O",
          12: "B"
      }
    }

    ВАЖНО:
    - замества Д/В/Н с O или B
    - НЕ пипа циклите
    - НЕ търси заместници
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
