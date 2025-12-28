import pytest

from scheduler.logic.generator.overrides import (
    ManualOverride,
    OverrideKind,
    index_overrides,
    get_override,
    WORKING_CODES,
    NON_WORKING_CODES,
)




def test_manual_override_creation():
    o = ManualOverride(
        employee="Иван",
        date=5,
        shift_code="D",
        kind=OverrideKind.SET_SHIFT,
        locked=True,
    )

    assert o.employee == "Иван"
    assert o.date == 5
    assert o.shift_code == "D"
    assert o.kind == OverrideKind.SET_SHIFT
    assert o.locked is True


def test_manual_override_is_frozen():

    o = ManualOverride("Иван", 5, "D", OverrideKind.SET_SHIFT, True)

    with pytest.raises(Exception):
        o.employee = "Петър"


def test_index_overrides_groups_by_day_and_employee():
    overrides = [
        ManualOverride("Иван", 5, "D", OverrideKind.SET_SHIFT),
        ManualOverride("Мария", 5, "V", OverrideKind.SET_SHIFT),
        ManualOverride("Петър", 10, "P", OverrideKind.VACATION),
    ]

    indexed = index_overrides(overrides)

    assert 5 in indexed
    assert 10 in indexed

    assert indexed[5]["Иван"].shift_code == "D"
    assert indexed[5]["Мария"].shift_code == "V"
    assert indexed[10]["Петър"].shift_code == "P"


def test_get_override_returns_item_if_exists():
    overrides = [
        ManualOverride("Иван", 3, "V", OverrideKind.SET_SHIFT),
    ]

    lookup = index_overrides(overrides)

    result = get_override(lookup, 3, "Иван")
    assert result is not None
    assert result.shift_code == "V"


def test_get_override_returns_none_if_not_exists():
    overrides = [
        ManualOverride("Иван", 3, "V", OverrideKind.SET_SHIFT),
    ]

    lookup = index_overrides(overrides)

    assert get_override(lookup, 3, "Мария") is None
    assert get_override(lookup, 10, "Иван") is None


def test_working_codes_definition():
    assert WORKING_CODES == {"D", "V", "N"}


def test_non_working_codes_definition():
    assert NON_WORKING_CODES == {"P", "VAC", "SICK", "OFF"}


