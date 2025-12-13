from scheduler.logic.rules import is_shift_allowed
from .data_model import EmployeeState

BLOCK_SIZE = 4
REST_AFTER_NIGHT = 3


def block_completed(state: EmployeeState) -> bool:
    return state.consecutive_same_shift >= BLOCK_SIZE


def is_in_rest_period(state: EmployeeState, new_shift: str) -> bool:

    if state.last_shift != "N":
        return False

    if state.days_since < REST_AFTER_NIGHT:
        return True


    if state.days_since == REST_AFTER_NIGHT and new_shift != "V":
        return True

    return False


def is_block_transition_allowed(state: EmployeeState, new_shift: str) -> bool:

    if state.last_shift is None:
        return True

    if not block_completed(state):
        # В рамките на блок → само същата смяна
        return state.last_shift == new_shift

    # Блокът е приключил → позволени ротации
    if state.last_shift == "D" and new_shift == "V":
        return True

    if state.last_shift == "V" and new_shift == "N":
        return True

    if state.last_shift == "N" and new_shift == "V":
        return True

    return False


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
        if name == admin_name:
            continue

        if name in used_today:
            continue


        if is_in_rest_period(st, shift_code):
            continue


        if not is_block_transition_allowed(st, shift_code):
            continue

        # допълнителна защита
        if not is_shift_allowed(st.last_shift, st.days_since, shift_code, crisis_mode):
            continue

        candidates.append((
            name,
            st.consecutive_same_shift,
            st.total_workdays,
            st.days_since
        ))

    if not candidates:
        return None


    candidates.sort(key=lambda x: (
        -x[1],
        x[2],
        -x[3],
        x[0]
    ))

    return candidates[0][0]
