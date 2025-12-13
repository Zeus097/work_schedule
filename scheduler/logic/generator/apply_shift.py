from .data_model import EmployeeState


def apply_shift(state: EmployeeState, shift: str, is_workday: bool):
    if shift in {"D", "V", "N", "A"}:
        if is_workday:
            state.total_workdays += 1
        state.last_shift = shift
        state.days_since_work = 0
        state.worked_yesterday = True
    else:
        state.days_since_work += 1
        state.worked_yesterday = False
