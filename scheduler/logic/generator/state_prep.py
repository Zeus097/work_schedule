from typing import Dict
from scheduler.logic.rules import to_lat, is_working_shift, get_preferred_next_shift
from .data_model import EmployeeState


def prepare_employee_states(config, last_month_data) -> Dict[str, EmployeeState]:
    states: Dict[str, EmployeeState] = {}

    for emp in config["employees"]:
        name = emp["name"]
        last_shift_raw = emp.get("last_shift")
        last_shift = to_lat(last_shift_raw) if last_shift_raw else None

        states[name] = EmployeeState(
            name=name,
            last_shift=last_shift,
            last_day=None,
            total_workdays=0,
            days_since=999,
            next_shift_ideal=get_preferred_next_shift(last_shift) if last_shift else None,
            consecutive_same_shift=1 if last_shift in {"D", "V", "N"} else 0
        )

    admin_name = config["admin"]["name"]
    states[admin_name] = EmployeeState(
        name=admin_name,
        last_shift="A",
        last_day=None,
        total_workdays=0,
        days_since=999,
        next_shift_ideal="A",
        consecutive_same_shift=1
    )


    if not last_month_data or "days" not in last_month_data:
        return states


    for emp_name, month_days in last_month_data["days"].items():
        if emp_name not in states:
            continue

        last_cons = 0
        last_shift = None


        for day in sorted(month_days, key=lambda x: int(x)):
            shift_lat = to_lat(month_days[day])

            if is_working_shift(shift_lat):

                if shift_lat == last_shift:
                    last_cons += 1
                else:
                    last_cons = 1

                last_shift = shift_lat
                states[emp_name].last_day = int(day)


        if last_shift:
            st = states[emp_name]
            st.last_shift = last_shift
            st.consecutive_same_shift = last_cons


    for st in states.values():
        if st.last_day is not None:
            st.days_since = 1

    return states







