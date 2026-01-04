from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any
import portalocker


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON файлът не съществува: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_json_with_lock(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        try:
            import os
            os.fsync(f.fileno())
        except OSError:
            pass
        portalocker.unlock(f)

    if path.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_suffix(path.suffix + f".bak-{timestamp}")
        path.replace(backup_path)

    tmp_path.replace(path)


# -------- paths --------
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_json_file(name: str) -> Dict[str, Any]:
    path = DATA_DIR / f"{name}.json"
    return _load_json(path)


def write_json_file(data: Dict[str, Any], name: str) -> None:
    path = DATA_DIR / f"{name}.json"
    _save_json_with_lock(path, data)
