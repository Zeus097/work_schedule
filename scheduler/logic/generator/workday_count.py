import calendar
from datetime import date


def count_working_days(year: int, month: int, holidays: set[date] | None = None) -> int:
    if holidays is None:
        holidays = set()

    _, days_in_month = calendar.monthrange(year, month)
    working_days = 0

    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        if d.weekday() < 5 and d not in holidays:
            working_days += 1

    return working_days



