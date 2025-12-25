def apply_overrides(schedule, overrides):
    """
        Applies manual shift overrides to a schedule in place.
        Updates specified employee/day entries with new shift values,
        ignoring unknown employee IDs, and returns the modified schedule.
    """

    for emp_id, days in overrides.items():
        emp_id = str(emp_id)
        if emp_id not in schedule:
            continue

        for day, shift in days.items():
            schedule[emp_id][str(day)] = shift

    return schedule
