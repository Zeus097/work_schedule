from scheduler.logic.generator.data_model import EmployeeState


def test_employee_state_initialization():
    st = EmployeeState(
        name="Тест",
        last_shift="D",
        last_day=15,
        total_workdays=10,
        days_since=3,
        next_shift_ideal="V",
        consecutive_same_shift=2,
    )

    assert st.name == "Тест"
    assert st.last_shift == "D"
    assert st.last_day == 15
    assert st.total_workdays == 10
    assert st.days_since == 3
    assert st.next_shift_ideal == "V"
    assert st.consecutive_same_shift == 2


def test_employee_state_optional_fields_allow_none():
    st = EmployeeState(
        name="Тест",
        last_shift=None,
        last_day=None,
        total_workdays=0,
        days_since=0,
        next_shift_ideal=None,
    )

    assert st.last_shift is None
    assert st.next_shift_ideal is None
    assert st.last_day is None



def test_employee_state_default_consecutive_count():

    st = EmployeeState(
        name="Тест",
        last_shift=None,
        last_day=None,
        total_workdays=0,
        days_since=0,
        next_shift_ideal=None,
    )

    assert st.consecutive_same_shift == 0



def test_employee_state_mutability():
    st = EmployeeState(
        name="Тест",
        last_shift="D",
        last_day=10,
        total_workdays=5,
        days_since=1,
        next_shift_ideal="V",
        consecutive_same_shift=1,
    )


    st.last_shift = "N"
    st.total_workdays += 1
    st.days_since = 0
    st.next_shift_ideal = "D"
    st.consecutive_same_shift = 2

    assert st.last_shift == "N"
    assert st.total_workdays == 6
    assert st.days_since == 0
    assert st.next_shift_ideal == "D"
    assert st.consecutive_same_shift == 2



