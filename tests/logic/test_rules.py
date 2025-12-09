import pytest
from scheduler.logic import rules


def test_to_lat_basic():
    assert rules.to_lat("Д") == "D"
    assert rules.to_lat("В") == "V"
    assert rules.to_lat("Н") == "N"
    assert rules.to_lat("А") == "A"
    assert rules.to_lat("О") == "O"
    assert rules.to_lat("") == "REST"
    assert rules.to_lat(" ") == "REST"
    assert rules.to_lat("-") == "REST"
    assert rules.to_lat(None) == "REST"


def test_to_cyr_basic():
    assert rules.to_cyr("D") == "Д"
    assert rules.to_cyr("V") == "В"
    assert rules.to_cyr("N") == "Н"
    assert rules.to_cyr("A") == "А"
    assert rules.to_cyr("O") == "О"
    assert rules.to_cyr("REST") == ""
    assert rules.to_cyr(None) == ""


def test_is_working_shift():
    assert rules.is_working_shift("D")
    assert rules.is_working_shift("V")
    assert rules.is_working_shift("N")
    assert rules.is_working_shift("A")
    assert not rules.is_working_shift("O")
    assert not rules.is_working_shift("REST")


def test_is_rest_like():
    assert rules.is_rest_like("O")
    assert rules.is_rest_like("REST")
    assert rules.is_rest_like(None)
    assert not rules.is_rest_like("D")
    assert not rules.is_rest_like("V")


def test_get_transition_rule_existing():
    r = rules.get_transition_rule("N")
    assert r.min_rest_days == 1
    assert r.preferred_rest_days == 2
    assert r.default_next == "V"


def test_get_transition_rule_unknown():
    r = rules.get_transition_rule("UNKNOWN")
    assert r.min_rest_days == 0
    assert r.preferred_rest_days == 0
    assert r.default_next is None


def test_get_preferred_next_shift():
    assert rules.get_preferred_next_shift("N") == "V"
    assert rules.get_preferred_next_shift("V") == "D"
    assert rules.get_preferred_next_shift("D") == "N"
    assert rules.get_preferred_next_shift("A") == "A"
    assert rules.get_preferred_next_shift("REST") is None
    assert rules.get_preferred_next_shift(None) is None




def test_shift_allowed_rest_always_ok():
    assert rules.is_shift_allowed("D", 0, "REST", False)
    assert rules.is_shift_allowed("N", 0, "O", True)


def test_shift_allowed_new_employee_anything_ok():
    assert rules.is_shift_allowed(None, 0, "D", False)
    assert rules.is_shift_allowed(None, 0, "N", True)
    assert rules.is_shift_allowed(None, 0, "A", False)


def test_shift_allowed_forbidden_evening_to_night():
    assert not rules.is_shift_allowed("V", 1, "N", False)


def test_shift_allowed_rest_requirement_normal_mode():
    assert not rules.is_shift_allowed("N", 0, "D", False)
    assert rules.is_shift_allowed("N", 2, "D", False)


def test_shift_allowed_rest_requirement_crisis_mode():
    assert not rules.is_shift_allowed("N", 0, "D", True)
    assert rules.is_shift_allowed("N", 1, "D", True)


def test_shift_allowed_real_shifts_default():
    assert rules.is_shift_allowed("D", 0, "V", False)
    assert rules.is_shift_allowed("V", 3, "D", False)



