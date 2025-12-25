from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from scheduler.logic.generator.apply_overrides import apply_overrides
from scheduler.logic.file_paths import DATA_DIR
from scheduler.logic.json_help_functions import _load_json, _save_json_with_lock

MONTH_PATTERN = re.compile(r"^(\d{4})-(\d{2})\.json$")



def get_month_path(year: int, month: int) -> Path:
    return DATA_DIR / f"{year:04d}-{month:02d}.json"


def save_month(year: int, month: int, data: Dict[str, Any]) -> None:
    """
    Saves month YYYY-MM.json (safe write).
    """
    path = get_month_path(year, month)
    _save_json_with_lock(path, data)


def load_month(year: int, month: int) -> Dict[str, Any]:
    path = get_month_path(year, month)
    data = _load_json(path)
    data.setdefault("schedule", {})
    data.setdefault("overrides", {})
    data.setdefault("ui_locked", False)
    data.setdefault("generator_locked", False)
    data["_runtime_schedule"] = apply_overrides(
        data["schedule"],
        data["overrides"]
    )

    return data



def list_month_files() -> List[Tuple[int, int, Path]]:
    """
        Returns list of existing month files (year, month, path).
    """
    result: List[Tuple[int, int, Path]] = []

    if not DATA_DIR.exists():
        return result

    for p in DATA_DIR.iterdir():
        if not p.is_file():
            continue

        m = MONTH_PATTERN.match(p.name)
        if not m:
            continue

        year = int(m.group(1))
        month = int(m.group(2))
        result.append((year, month, p))

    result.sort(key=lambda x: (x[0], x[1]))
    return result


def get_latest_month() -> Optional[Tuple[int, int, Dict[str, Any]]]:
    """
        Returns (year, month, data) for the last available month.
    """
    months = list_month_files()
    if not months:
        return None

    year, month, path = months[-1]
    data = _load_json(path)

    return year, month, data



