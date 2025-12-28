import pytest
from scheduler.logic import rules


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


def test_get_transition_rule_unknown():
    r = rules.get_transition_rule("UNKNOWN")
    assert r.min_rest_days == 0
    assert r.preferred_rest_days == 0
    assert r.default_next is None


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



