from pathlib import Path
from django.conf import settings

DATA_DIR = Path(settings.BASE_DIR) / "data"
DATA_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.json"
