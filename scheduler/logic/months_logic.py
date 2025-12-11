from __future__ import annotations
from scheduler.logic.generator.apply_overrides import apply_overrides
from scheduler.logic.file_paths import DATA_DIR
import re

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from scheduler.logic.json_help_functions import _load_json, _save_json_with_lock




MONTH_PATTERN = re.compile(r"^(\d{4})-(\d{2})\.json$")


def get_month_path(year: int, month: int) -> Path:
    return DATA_DIR / f"{year:04d}-{month:02d}.json"


def save_month(year: int, month: int, data: Dict[str, Any]) -> None:
    """
    Saves month file 'YYYY-MM.json' safely.
    """

    path = get_month_path(year, month)
    _save_json_with_lock(path, data)


def load_month(year: int, month: int) -> Dict[str, Any]:
    """
    Reades month file 'YYYY-MM.json'. Raise 'FileNotFoundError' if missing.
    """

    path = get_month_path(year, month)
    data = _load_json(path)

    # ensure overrides exists
    if "overrides" not in data:
        data["overrides"] = {}

    # apply overrides
    data["schedule"] = apply_overrides(
        data["schedule"],
        data["overrides"]
    )

    return data




def list_month_files() -> List[Tuple[int, int, Path]]:
    """
    Returns a list (year, month, path) for every available ;YYYY-MM.json; files in data/.
    """

    result: List[Tuple[int, int, Path]] = []

    for p in DATA_DIR.iterdir():

        if not p.is_file():
            continue

        match = MONTH_PATTERN.match(p.name)

        if not match:
            continue

        year, month = int(match.group(1)), int(match.group(2))
        result.append((year, month, p))

    # sort by Y/M
    result.sort(key=lambda t: (t[0], t[1]))

    return result


def get_latest_month() -> Optional[Tuple[int, int, Dict[str, Any]]]:
    """
    Returns the last available month (year, month, data) or None if not exists.
    """

    months = list_month_files()
    if not months:
        return None

    year, month, path = months[-1]
    data = _load_json(path)

    return year, month, data


