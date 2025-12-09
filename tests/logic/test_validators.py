import pytest
from scheduler.logic.validators import (
    validate_shift,
    validate_admin_shift,
    validate_month,
)
from scheduler.logic.rules import to_lat


def test_validate_shift_wraps_is_shift_allowed():
    assert validate_shift(None, 0, "D", False)
    assert not validate_shift("V", 0, "N", False)
    assert validate_shift("N", 2, "D", False)


def test_validate_admin_shift_rest_ok():
    assert validate_admin_shift(0, "REST")
    assert validate_admin_shift(3, "O")
    assert validate_admin_shift(2, None)


def test_validate_admin_shift_only_A_weekdays():
    assert validate_admin_shift(0, "A")
    assert validate_admin_shift(4, "A")
    assert not validate_admin_shift(5, "A")
    assert not validate_admin_shift(6, "A")


def test_validate_admin_shift_disallow_other_working_shifts():
    assert not validate_admin_shift(2, "D")
    assert not validate_admin_shift(2, "V")
    assert not validate_admin_shift(2, "N")


def test_validate_month_valid_sequence():
    schedule = {
        "Иван": {
            1: "Д",
            2: "В",
            3: "Д",
        }
    }
    weekdays = {1: 0, 2: 1, 3: 2}
    errors = validate_month(schedule, False, weekdays)
    assert errors == []



def test_validate_month_invalid_rotation():
    schedule = {
        "Иван": {
            1: "В",
            2: "Н",
        }
    }
    weekdays = {1: 0, 2: 1}
    errors = validate_month(schedule, False, weekdays)
    assert len(errors) == 1
    assert errors[0][0] == "Иван"
    assert errors[0][1] == 2


def test_validate_month_admin_rules():
    schedule = {
        "Администратор": {
            1: "А",
            2: "А",
            6: "Д",
        }
    }
    weekdays = {1: 0, 2: 3, 6: 5}
    errors = validate_month(schedule, False, weekdays)

    assert len(errors) == 1
    assert errors[0][0].lower().startswith("адм")
    assert errors[0][1] == 6


