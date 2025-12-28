import pytest
import calendar

from scheduler.logic.generator.generator import generate_new_month




@pytest.fixture
def employees_ok():
    return {
        "1": "Admin",
        "2": "Emp 1",
        "3": "Emp 2",
        "4": "Emp 3",
        "5": "Emp 4",
    }


@pytest.fixture
def month_data_with_admin(monkeypatch):
    def fake_load_month(year, month):
        return {
            "month_admin_id": "1"
        }

    monkeypatch.setattr(
        "scheduler.logic.generator.generator.load_month",
        fake_load_month
    )


@pytest.fixture
def no_last_cycle(monkeypatch):
    monkeypatch.setattr(
        "scheduler.logic.generator.generator.load_last_cycle_state",
        lambda: {}
    )


@pytest.fixture
def no_holidays(monkeypatch):
    monkeypatch.setattr(
        "scheduler.logic.generator.generator.get_holidays_for_month",
        lambda y, m: []
    )


def test_no_admin_raises(employees_ok, monkeypatch):
    monkeypatch.setattr(
        "scheduler.logic.generator.generator.load_month",
        lambda y, m: {}
    )

    with pytest.raises(RuntimeError, match="Няма зададен администратор"):
        generate_new_month(2025, 1, employees_ok)


def test_admin_not_active_raises(employees_ok, month_data_with_admin, monkeypatch):
    employees_ok.pop("1")  # администраторът липсва

    with pytest.raises(RuntimeError, match="Администраторът не е активен"):
        generate_new_month(2025, 1, employees_ok)


def test_less_than_4_workers_raises(month_data_with_admin, monkeypatch):
    employees = {
        "1": "Admin",
        "2": "Emp 1",
        "3": "Emp 2",
        "4": "Emp 3",
    }

    with pytest.raises(RuntimeError, match="минимум 4"):
        generate_new_month(2025, 1, employees)


def test_successful_generation_structure(
    employees_ok,
    month_data_with_admin,
    no_last_cycle,
    no_holidays
):
    result = generate_new_month(2025, 1, employees_ok)

    assert result["year"] == 2025
    assert result["month"] == 1
    assert result["generator_locked"] is True
    assert result["month_admin_id"] == "1"

    schedule = result["schedule"]
    assert set(schedule.keys()) == set(employees_ok.keys())


def test_each_day_has_required_shifts(
    employees_ok,
    month_data_with_admin,
    no_last_cycle,
    no_holidays
):
    year, month = 2025, 1
    result = generate_new_month(year, month, employees_ok)
    schedule = result["schedule"]

    _, days_in_month = calendar.monthrange(year, month)

    for day in range(1, days_in_month + 1):
        shifts = []
        for emp, days in schedule.items():
            s = days[str(day)]
            if s in ("Д", "В", "Н"):
                shifts.append(s)

        assert sorted(shifts) == ["В", "Д", "Н"], f"Day {day} broken"


def test_admin_shift_only_weekdays(
    employees_ok,
    month_data_with_admin,
    no_last_cycle,
    no_holidays
):
    year, month = 2025, 1
    result = generate_new_month(year, month, employees_ok)
    admin_days = result["schedule"]["1"]

    for day, shift in admin_days.items():
        weekday = calendar.weekday(year, month, int(day))
        if weekday < 5:
            assert shift == "А"
        else:
            assert shift == ""


def test_strict_false_does_not_crash_on_missing(monkeypatch, employees_ok):
    monkeypatch.setattr(
        "scheduler.logic.generator.generator.load_month",
        lambda y, m: {"month_admin_id": "1"}
    )

    monkeypatch.setattr(
        "scheduler.logic.generator.generator.get_holidays_for_month",
        lambda y, m: []
    )

    monkeypatch.setattr(
        "scheduler.logic.generator.generator.load_last_cycle_state",
        lambda: {}
    )

    generate_new_month(2025, 1, employees_ok, strict=False)


