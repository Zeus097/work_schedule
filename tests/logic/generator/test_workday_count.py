from datetime import date
from scheduler.logic.generator.workday_count import count_working_days




def test_count_working_days_simple_month():

    result = count_working_days(2026, 1)
    assert result == 22


def test_count_working_days_february_non_leap():

    assert count_working_days(2025, 2) == 20


def test_count_working_days_leap_year():
    # February 2024 is a leap year --> 21 working days
    assert count_working_days(2024, 2) == 21




def test_excludes_holidays_on_weekdays():
    holidays = {date(2026, 1, 2)}  # Петък → работен ден → броят се намалява
    assert count_working_days(2026, 1, holidays) == 21


def test_holiday_on_weekend_does_not_change_count():

    holidays = {date(2026, 1, 4)}
    assert count_working_days(2026, 1, holidays) == 22



def test_full_month_all_holidays():

    all_holidays = set()
    for day in range(1, 32):
        try:
            d = date(2026, 3, day)
            if d.weekday() < 5:
                all_holidays.add(d)
        except ValueError:
            pass

    assert count_working_days(2026, 3, all_holidays) == 0


def test_month_with_no_working_days():

    holidays = {date(2026, 4, day) for day in range(1, 31)}
    assert count_working_days(2026, 4, holidays) == 0



