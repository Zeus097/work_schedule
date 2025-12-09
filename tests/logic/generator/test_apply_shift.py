import pytest
from unittest.mock import patch

from scheduler.logic.generator.data_model import EmployeeState
from scheduler.logic.generator.apply_shift import apply_shift




def make_state(
    last_shift=None,
    last_day=None,
    total=0,
    since=0,
    consec=0,
    ideal=None,
):
    return EmployeeState(
        name="Тест",
        last_shift=last_shift,
        last_day=last_day,
        total_workdays=total,
        days_since=since,
        next_shift_ideal=ideal,
        consecutive_same_shift=consec,
    )




@pytest.mark.parametrize("shift", ["D", "V", "N", "A"])
def test_apply_shift_working_increments_workdays(shift):
    st = make_state(total=0)

    with patch("scheduler.logic.generator.apply_shift.get_preferred_next_shift", return_value="X"):
        apply_shift(st, shift, is_workday=True)

    assert st.total_workdays == 1
    assert st.last_shift == shift
    assert st.days_since == 0
    assert st.next_shift_ideal == "X"


def test_apply_shift_consecutive_increases_if_same_shift():
    st = make_state(last_shift="D", consec=2)

    with patch("scheduler.logic.rules.get_preferred_next_shift", return_value="X"):
        apply_shift(st, "D", is_workday=True)

    assert st.consecutive_same_shift == 3


def test_apply_shift_consecutive_resets_if_different_shift():
    st = make_state(last_shift="D", consec=5)

    with patch("scheduler.logic.rules.get_preferred_next_shift", return_value="X"):
        apply_shift(st, "V", is_workday=True)

    assert st.consecutive_same_shift == 1
    assert st.last_shift == "V"


def test_apply_shift_sets_last_shift():
    st = make_state(last_shift="V")

    with patch("scheduler.logic.rules.get_preferred_next_shift", return_value="X"):
        apply_shift(st, "N", is_workday=True)

    assert st.last_shift == "N"




@pytest.mark.parametrize("shift", ["REST", "P", "SICK", "OFF", "VAC"])
def test_apply_shift_non_working_increases_days_since(shift):
    st = make_state(since=2)

    apply_shift(st, shift, is_workday=False)

    assert st.days_since == 3
    assert st.consecutive_same_shift == 0
    assert st.last_shift == shift


def test_apply_shift_rest_does_not_increment_workdays():
    st = make_state(total=10)

    apply_shift(st, "REST", is_workday=False)

    assert st.total_workdays == 10




def test_apply_shift_sets_next_shift_ideal():
    st = make_state()

    with patch("scheduler.logic.rules.get_preferred_next_shift", return_value="N"):
        apply_shift(st, "D", is_workday=True)

    assert st.next_shift_ideal == "N"
