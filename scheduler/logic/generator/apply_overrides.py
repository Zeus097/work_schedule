def apply_overrides(schedule, overrides):
    for emp_id, days in overrides.items():
        emp_id = str(emp_id)
        if emp_id not in schedule:
            continue

        for day, shift in days.items():
            schedule[emp_id][str(day)] = shift

    return schedule
