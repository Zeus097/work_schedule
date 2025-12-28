from pathlib import Path
import sys


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return Path(__file__).resolve().parents[2]


def get_data_dir() -> Path:
    data = get_app_root() / "data"
    data.mkdir(exist_ok=True)
    return data


