from pathlib import Path
from scheduler.utils.runtime_paths import project_root


BASE_DIR = project_root()

DATA_DIR = BASE_DIR / "runtime_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.json"
