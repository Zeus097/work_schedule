# scheduler/logic/lock/month_lock.py

import calendar
from datetime import date
from scheduler.models import MonthRecord
from scheduler.logic.cycle_state import save_last_cycle_state


def lock_month(year: int, month: int) -> None:
    record = MonthRecord.objects.get(year=year, month=month)

    # ❌ вече заключен
    if record.data.get("generator_locked") is True:
        raise RuntimeError("Месецът вече е заключен.")

    schedule = record.data["schedule"]

    # последен ден от месеца
    _, last_day = calendar.monthrange(year, month)
    last_date = date(year, month, last_day)

    # записваме cycle state
    save_last_cycle_state(schedule, last_date)

    # маркираме месеца като заключен
    record.data["generator_locked"] = True
    record.save(update_fields=["data"])
