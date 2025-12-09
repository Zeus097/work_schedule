import django
from django.conf import settings


if not settings.configured:
    settings.configure(
        BASE_DIR="",
        INSTALLED_APPS=[],
    )
    django.setup()


import pytest
from unittest.mock import patch, MagicMock

from scheduler.logic.generator.generator import generate_new_month
from scheduler.logic.generator.overrides import ManualOverride, OverrideKind




def make_config():
    return {
        "employees": [
            {"name": "Служител 1"},
            {"name": "Служител 2"},
            {"name": "Служител 3"},
        ],
        "admin": {"name": "Администратор"},
    }


def make_states():
    mock_state = MagicMock()
    mock_state.days_since = 0
    return {
        "Служител 1": mock_state,
        "Служител 2": mock_state,
        "Служител 3": mock_state,
        "Администратор": mock_state,
    }



@patch("scheduler.logic.generator.generator.apply_shift")
@patch("scheduler.logic.generator.generator.choose_employee_for_shift")
@patch("scheduler.logic.generator.generator.prepare_employee_states")
@patch("scheduler.logic.generator.generator.count_working_days")
@patch("scheduler.logic.generator.generator.get_latest_month")
@patch("scheduler.logic.generator.generator.load_config")
def test_generator_respects_overrides(
    mock_load_config,
    mock_get_last,
    mock_count_workdays,
    mock_prepare_states,
    mock_choose,
    mock_apply_shift,
):

    mock_load_config.return_value = make_config()
    mock_get_last.return_value = None
    mock_count_workdays.return_value = 22
    mock_prepare_states.return_value = make_states()


    def choose_side_effect(*args, **kwargs):

        used = kwargs.get("used_today", set())


        for candidate in ["Служител 2", "Служител 3", "Служител 1"]:
            if candidate not in used:
                return candidate

    mock_choose.side_effect = choose_side_effect

    overrides = [
        ManualOverride("Служител 1", 5, "D", OverrideKind.SET_SHIFT, True),
        ManualOverride("Служител 2", 10, "P", OverrideKind.VACATION, True),
        ManualOverride("Служител 3", 3, "V", OverrideKind.SET_SHIFT, True),
    ]


    result = generate_new_month(2026, 1, overrides=overrides)
    schedule = result["schedule"]




    assert schedule["Служител 1"][5] == "Д"


    assert schedule["Служител 2"][10] == "П"


    assert schedule["Служител 3"][3] == "В"


    assert schedule["Администратор"][1] == "А"


    assert schedule["Администратор"][4] == ""


    assert "schedule" in result
    assert "ideal" in result
    assert "states" in result



