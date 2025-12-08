from scheduler.logic.rules import get_preferred_next_shift
from .data_model import EmployeeState


def apply_shift(state: EmployeeState, shift_code: str, is_workday: bool):

    if shift_code in {"D", "V", "N", "A"}:

        if state.last_shift == shift_code:
            state.consecutive_same_shift += 1
        else:
            state.consecutive_same_shift = 1

        if is_workday:
            state.total_workdays += 1

        state.days_since = 0
        state.last_shift = shift_code
        state.next_shift_ideal = get_preferred_next_shift(shift_code)

    else:
        state.consecutive_same_shift = 0
        state.days_since += 1
        state.last_shift = shift_code



