from pathlib import Path

APP_NAME = "Kantar247"

# Runtime root (Application Support)
RUNTIME_DATA_DIR = (
    Path.home()
    / "Library"
    / "Application Support"
    / APP_NAME
)
RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Django paths
BASE_DIR = Path(__file__).resolve().parent


DATA_DIR = RUNTIME_DATA_DIR

SECRET_KEY = "desktop-app-secret-key"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "weight_department_schedule.scheduler",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": RUNTIME_DATA_DIR / "db.sqlite3",
    }
}

USE_TZ = True
TIME_ZONE = "Europe/Sofia"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
