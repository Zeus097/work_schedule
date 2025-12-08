from scheduler.logic.rules import is_shift_allowed
from .data_model import EmployeeState

MAX_CONSECUTIVE_SAME_SHIFT = 4
ADMIN_MAX_CONSECUTIVE_SAME_SHIFT = 5


def is_consecutive_allowed(state: EmployeeState, new_shift: str, is_admin: bool) -> bool:
    if new_shift not in {"D", "V", "N"}:
        return True

    if state.last_shift == new_shift:
        next_cons = state.consecutive_same_shift + 1
    else:
        next_cons = 1

    limit = ADMIN_MAX_CONSECUTIVE_SAME_SHIFT if is_admin else MAX_CONSECUTIVE_SAME_SHIFT
    return next_cons <= limit


def is_within_workday_limits(state: EmployeeState, is_admin: bool,
                             soft_min: int, soft_max: int,
                             hard_min: int, hard_max: int,
                             crisis_mode: bool) -> bool:

    if state.last_shift is None:
        return True

    if is_admin:
        return True

    days = state.total_workdays

    if days > hard_max:
        return False

    if days > soft_max and not crisis_mode:
        return False

    return True


def choose_employee_for_shift(
    states,
    shift_code,
    admin_name,
    used_today,
    crisis_mode,
    soft_min, soft_max, hard_min, hard_max
):
    candidates = []

    for name, st in states.items():
        is_admin = (name == admin_name)

        if is_admin:
            continue

        if name in used_today:
            continue

        if st.last_shift == "V" and shift_code == "N":
            continue

        if not is_shift_allowed(st.last_shift, st.days_since, shift_code, crisis_mode):
            continue

        if not is_consecutive_allowed(st, shift_code, is_admin):
            continue

        if not is_within_workday_limits(st, is_admin, soft_min, soft_max, hard_min, hard_max, crisis_mode):
            continue

        ideal_match = 1 if st.next_shift_ideal == shift_code else 0

        candidates.append((
            name,
            -ideal_match,
            -st.days_since,
            st.total_workdays
        ))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[1], x[2], x[3], x[0]))
    return candidates[0][0]





