import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        # .app/Contents/MacOS/app
        exe_path = Path(sys.executable).resolve()
        return exe_path.parent
    return Path(__file__).resolve().parents[2]



def storage_dir() -> Path:
    return project_root() / "storage"


def docs_dir() -> Path:
    return project_root() / "docs"


def generator_data_dir() -> Path:
    return project_root() / "scheduler" / "logic" / "generator" / "data"
