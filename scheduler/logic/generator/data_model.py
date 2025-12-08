from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmployeeState:
    name: str
    last_shift: Optional[str]
    last_day: Optional[int]
    total_workdays: int
    days_since: int
    next_shift_ideal: Optional[str]
    consecutive_same_shift: int = 0


