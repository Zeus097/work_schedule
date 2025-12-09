import pytest
from unittest.mock import patch

from scheduler.logic.generator.state_prep import prepare_employee_states
from scheduler.logic.generator.data_model import EmployeeState




@patch("scheduler.logic.generator.state_prep.get_preferred_next_shift")
@patch("scheduler.logic.generator.state_prep.is_working_shift")
@patch("scheduler.logic.generator.state_prep.to_lat")
def test_prepare_initial_states_basic(mock_to_lat, mock_working, mock_next):
    mock_to_lat.side_effect = lambda x: x  # identity
    mock_next.side_effect = lambda x: "NEXT"
    mock_working.return_value = True

    config = {
        "employees": [
            {"name": "Иван", "last_shift": "Д"},  # Cyrillic → NOT working shift
            {"name": "Мария", "last_shift": None},
        ],
        "admin": {"name": "Администратор"},
    }

    states = prepare_employee_states(config, last_month_data=None)


    st = states["Иван"]
    assert st.last_shift == "Д"

    assert st.consecutive_same_shift == 0
    assert st.days_since == 999
    assert st.next_shift_ideal == "NEXT"


    st2 = states["Мария"]
    assert st2.last_shift is None
    assert st2.consecutive_same_shift == 0
    assert st2.days_since == 999
    assert st2.next_shift_ideal is None


    st_admin = states["Администратор"]
    assert st_admin.last_shift == "A"
    assert st_admin.next_shift_ideal == "A"
    assert st_admin.consecutive_same_shift == 1




@patch("scheduler.logic.generator.state_prep.get_preferred_next_shift")
@patch("scheduler.logic.generator.state_prep.is_working_shift")
@patch("scheduler.logic.generator.state_prep.to_lat")
def test_prepare_states_from_last_month(mock_to_lat, mock_working, mock_next):
    mock_to_lat.side_effect = lambda x: x  # identity
    mock_working.side_effect = lambda x: x in {"D", "V", "N"}
    mock_next.return_value = "NEXT"

    config = {
        "employees": [
            {"name": "Иван", "last_shift": None},
        ],
        "admin": {"name": "Администратор"},
    }

    last_month_data = {
        "days": {
            "Иван": {
                1: "D",
                2: "D",
                3: "V",
            }
        }
    }

    states = prepare_employee_states(config, last_month_data)
    st = states["Иван"]


    assert st.last_shift == "V"
    assert st.last_day == 3


    assert st.consecutive_same_shift == 3


    assert st.days_since == 1




@patch("scheduler.logic.generator.state_prep.to_lat", lambda x: x)
@patch("scheduler.logic.generator.state_prep.is_working_shift", lambda x: True)
@patch("scheduler.logic.generator.state_prep.get_preferred_next_shift", lambda x: "NEXT")
def test_state_prep_ignores_missing_employees():
    config = {
        "employees": [
            {"name": "Иван", "last_shift": None},
        ],
        "admin": {"name": "Администратор"},
    }

    last_month_data = {
        "days": {
            "Несъществуващ": {1: "D"},
        }
    }

    states = prepare_employee_states(config, last_month_data)


    st = states["Иван"]
    assert st.last_shift is None
    assert st.last_day is None
    assert st.days_since == 999
    assert st.consecutive_same_shift == 0



