from __future__ import annotations

import calendar

from scheduler.logic.configuration_helpers import load_config
from scheduler.logic.months_logic import get_latest_month
from scheduler.logic.generator.overrides import (
    index_overrides,
    get_override,
    WORKING_CODES,
    NON_WORKING_CODES,
)

# Pattern:
# D -> rest(1) -> N -> rest(2) -> V -> rest(1) -> D -> ...
# Important: the day marked "N" is the day the person worked 00:00-08:00.
# After that day there are exactly 2 empty rest days, then starts "V".
REST_AFTER_D = 1
REST_AFTER_V = 1
REST_AFTER_N = 2

CYR = {"D": "Д", "V": "В", "N": "Н"}
LAT = {v: k for k, v in CYR.items()}

def _next_after(last_shift: str | None) -> str:
    # Rotation: D -> N -> V -> D
    if last_shift == "D":
        return "N"
    if last_shift == "N":
        return "V"
    if last_shift == "V":
        return "D"
    # new employee -> will be seeded elsewhere
    return "D"

def _rest_after(shift: str) -> int:
    if shift == "N":
        return REST_AFTER_N
    if shift == "D":
        return REST_AFTER_D
    if shift == "V":
        return REST_AFTER_V
    return 0

def _seed_shift_for_name(name: str) -> str:
    # stable distribution across D/V/N
    s = sum(ord(c) for c in name)
    return ("D", "V", "N")[s % 3]

def _extract_last_shift_from_month(month_days: dict) -> str | None:
    # month_days: {"1":"Д", ...} or {"1":"", ...}
    last = None
    for d in sorted(month_days.keys(), key=lambda x: int(x)):
        v = month_days[d]
        if v in ("Д", "В", "Н"):
            last = LAT[v]
    return last

def generate_new_month(year: int, month: int, overrides=None):
    config = load_config()

    latest = get_latest_month()
    last_month_data = latest[2] if latest else None  # whatever storage returns

    _, num_days = calendar.monthrange(year, month)

    workers = [emp["name"] for emp in config["employees"]]
    admin_name = config["admin"]["name"]

    schedule = {name: {day: "" for day in range(1, num_days + 1)} for name in workers}
    schedule[admin_name] = {day: "" for day in range(1, num_days + 1)}

    # overrides index
    override_index = index_overrides(overrides or [])

    # admin working days (delnik only)
    weekdays = {day: calendar.weekday(year, month, day) for day in range(1, num_days + 1)}
    holidays = set()  # if later you add holidays, plug them here

    def admin_is_on(day: int) -> bool:
        return (weekdays[day] < 5) and (day not in holidays)

    for day in range(1, num_days + 1):
        schedule[admin_name][day] = "А" if admin_is_on(day) else ""

    # --- init worker state (independent from EmployeeState to avoid breakage) ---
    last_shift: dict[str, str | None] = {n: None for n in workers}
    rest_left: dict[str, int] = {n: 0 for n in workers}
    seed_shift: dict[str, str] = {n: _seed_shift_for_name(n) for n in workers}

    if last_month_data and isinstance(last_month_data, dict):
        # accept both {"days": {...}} and {"schedule": {...}} shapes
        days_blob = last_month_data.get("days") or last_month_data.get("schedule") or {}
        if isinstance(days_blob, dict):
            for name in workers:
                mdays = days_blob.get(name)
                if isinstance(mdays, dict):
                    ls = _extract_last_shift_from_month(mdays)
                    if ls in ("D", "V", "N"):
                        last_shift[name] = ls
                        # after finishing last shift in prev month -> must rest at month start
                        rest_left[name] = _rest_after(ls)

    # --- helpers for choosing employees ---
    def desired_shift_for(name: str) -> str:
        ls = last_shift[name]
        if ls is None:
            return seed_shift[name]
        return _next_after(ls)

    def is_available(name: str, target_shift: str, allow_crisis: bool) -> bool:
        # If resting -> not available unless crisis
        if rest_left[name] > 0 and not allow_crisis:
            return False

        # Must follow rotation unless crisis
        want = desired_shift_for(name)
        if want != target_shift and not allow_crisis:
            return False

        return True

    def score(name: str) -> tuple:
        # Prefer those with more rest already done (lower rest_left),
        # then stable by name (simple, predictable)
        return (rest_left[name], name)

    # --- main day loop ---
    for day in range(1, num_days + 1):
        # determine required shifts for the day
        required = ["N", "V"]  # always must have N and V
        if not admin_is_on(day):
            # weekend/holiday: admin not there -> D must be covered by shifts team
            required.append("D")

        # locked overrides for today (per worker)
        locked: dict[str, str] = {}
        for name in workers:
            ov = get_override(override_index, day, name)
            if not ov:
                continue
            if ov.shift_code in WORKING_CODES:
                locked[name] = ov.shift_code  # "D"/"V"/"N"
            elif ov.shift_code in NON_WORKING_CODES:
                locked[name] = "REST"

        assigned: dict[str, str] = {}  # shift -> name
        used = set()

        # 1) apply locked working shifts first
        for name, val in locked.items():
            if val in ("D", "V", "N") and val in required:
                if val not in assigned and name not in used:
                    assigned[val] = name
                    used.add(name)

        # 2) fill remaining required shifts
        for sh in required:
            if sh in assigned:
                continue

            # normal pick (strict)
            candidates = [
                n for n in workers
                if n not in used
                and locked.get(n) != "REST"
                and (locked.get(n) in (None, sh))
                and is_available(n, sh, allow_crisis=False)
            ]
            if not candidates:
                # crisis pick (can break rest/rotation to avoid gaps)
                candidates = [
                    n for n in workers
                    if n not in used
                    and locked.get(n) != "REST"
                    and (locked.get(n) in (None, sh))
                    and is_available(n, sh, allow_crisis=True)
                ]

            if candidates:
                candidates.sort(key=score)
                chosen = candidates[0]
                assigned[sh] = chosen
                used.add(chosen)
            else:
                # If even crisis can't fill -> leave unfilled (should happen only with heavy lock/rest)
                # We do NOT crash; better to return something.
                pass

        # 3) write schedule + update rotation/rest
        for name in workers:
            # override REST forces empty cell
            if locked.get(name) == "REST":
                schedule[name][day] = ""
                # consume one rest day if they were already resting
                if rest_left[name] > 0:
                    rest_left[name] -= 1
                continue

            # assigned?
            worked_shift = None
            for sh, emp in assigned.items():
                if emp == name:
                    worked_shift = sh
                    break

            if worked_shift is None:
                # rest day
                schedule[name][day] = ""
                if rest_left[name] > 0:
                    rest_left[name] -= 1
                continue

            # work day
            schedule[name][day] = CYR[worked_shift]
            last_shift[name] = worked_shift
            rest_left[name] = _rest_after(worked_shift)

    # optional debug states
    states_dump = {}
    for name in workers + [admin_name]:
        if name == admin_name:
            states_dump[name] = {"type": "admin"}
        else:
            states_dump[name] = {
                "last_shift": last_shift[name],
                "rest_left": rest_left[name],
                "desired_next": desired_shift_for(name),
            }

    return {
        "schedule": schedule,
        "states": states_dump,
    }
