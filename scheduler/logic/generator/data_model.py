from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmployeeState:
    name: str

    last_shift: Optional[str]   # "D" / "V" / "N" / "A" / None
    last_day: Optional[int]

    total_workdays: int

    days_since_work: int
    worked_yesterday: bool

    current_block_shift: Optional[str]
    block_days_left: int

    rest_days_left: int

    seed_start_shift: str       # "D" / "V" / "N"
