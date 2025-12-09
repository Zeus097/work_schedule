import pytest
from unittest.mock import patch, MagicMock

from scheduler.logic.generator.limits import (
    is_consecutive_allowed,
    is_within_workday_limits,
    choose_employee_for_shift,
)
from scheduler.logic.generator.data_model import EmployeeState




def make_state(last_shift=None, consec=0, days_since=0, total=0, ideal=None):
    return EmployeeState(
        name="X",
        last_shift=last_shift,
        last_day=None,
        total_workdays=total,
        days_since=days_since,
        next_shift_ideal=ideal,
        consecutive_same_shift=consec,
    )




def test_consecutive_allowed_respects_limit():
    st = make_state(last_shift="D", consec=3)

    assert is_consecutive_allowed(st, "D", is_admin=False) is True

    # Next will be 5 -> limit is 4 → not allowed
    st2 = make_state(last_shift="D", consec=4)
    assert is_consecutive_allowed(st2, "D", is_admin=False) is False


def test_consecutive_allowed_admin_has_higher_limit():
    st = make_state(last_shift="D", consec=4)
    assert is_consecutive_allowed(st, "D", is_admin=True) is True
    st2 = make_state(last_shift="D", consec=5)
    assert is_consecutive_allowed(st2, "D", is_admin=True) is False


def test_consecutive_allowed_resets_for_new_shift():
    st = make_state(last_shift="D", consec=4)
    assert is_consecutive_allowed(st, "V", is_admin=False) is True




def test_workday_limits_allows_admin_always():
    st = make_state(total=999)
    assert is_within_workday_limits(st, True, 10, 12, 8, 15, False) is True


def test_workday_limits_hard_max_rejects():
    st = make_state(total=20, last_shift="D")
    assert is_within_workday_limits(st, False, 10, 12, 5, 15, False) is False



def test_workday_limits_soft_max_rejects_without_crisis():
    st = make_state(total=13, last_shift="D")
    assert is_within_workday_limits(st, False, 10, 12, 5, 15, False) is False


def test_workday_limits_soft_max_allows_with_crisis():
    st = make_state(total=13, last_shift="D")
    assert is_within_workday_limits(st, False, 10, 12, 5, 15, True) is True




@patch("scheduler.logic.generator.limits.is_shift_allowed")
def test_choose_employee_basic_ranking(mock_allowed):
    mock_allowed.return_value = True

    states = {
        "Иван": make_state(last_shift="D", consec=1, days_since=2, total=5, ideal="V"),
        "Мария": make_state(last_shift="V", consec=1, days_since=3, total=5, ideal="V"),
    }

    # No admin
    admin = "Админ"

    result = choose_employee_for_shift(
        states=states,
        shift_code="V",
        admin_name=admin,
        used_today=set(),
        crisis_mode=False,
        soft_min=0, soft_max=10, hard_min=0, hard_max=20
    )

    assert result == "Мария"


@patch("scheduler.logic.generator.limits.is_shift_allowed")
def test_choose_employee_blocks_used_today(mock_allowed):
    mock_allowed.return_value = True

    states = {
        "Иван": make_state(last_shift="D", consec=1, days_since=2, total=5),
        "Мария": make_state(last_shift="V", consec=1, days_since=3, total=5),
    }

    result = choose_employee_for_shift(
        states=states,
        shift_code="V",
        admin_name="Админ",
        used_today={"Мария"},  # blocked
        crisis_mode=False,
        soft_min=0, soft_max=10, hard_min=0, hard_max=20,
    )

    assert result == "Иван"


@patch("scheduler.logic.generator.limits.is_shift_allowed")
def test_choose_employee_returns_none_if_no_candidates(mock_allowed):
    mock_allowed.return_value = False  # никой не е позволен

    states = {
        "Иван": make_state(),
        "Мария": make_state(),
    }

    result = choose_employee_for_shift(
        states=states,
        shift_code="D",
        admin_name="Админ",
        used_today=set(),
        crisis_mode=False,
        soft_min=0, soft_max=10, hard_min=0, hard_max=20,
    )

    assert result is None


@patch("scheduler.logic.generator.limits.is_shift_allowed")
def test_choose_employee_disallows_V_to_N(mock_allowed):
    mock_allowed.return_value = True

    states = {
        "Иван": make_state(last_shift="D"),
        "Мария": make_state(last_shift="V"),
    }

    result = choose_employee_for_shift(
        states,
        shift_code="N",
        admin_name="Админ",
        used_today=set(),
        crisis_mode=False,
        soft_min=0, soft_max=10,
        hard_min=0, hard_max=20,
    )

    assert result == "Иван"



