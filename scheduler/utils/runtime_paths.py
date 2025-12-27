import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def project_root() -> Path:
    return app_root()


def storage_dir() -> Path:
    return project_root() / "storage"


def docs_dir() -> Path:
    return project_root() / "docs"


def generator_data_dir() -> Path:
    return project_root() / "scheduler" / "logic" / "generator" / "data"
