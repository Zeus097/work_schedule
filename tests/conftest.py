import os
import django
import pytest



@pytest.fixture
def sample_config():
    return {
        "employees": [
            {"name": "Служител 1", "start_date": "2025-01-01", "last_shift": None},
            {"name": "Служител 2", "start_date": "2025-01-01", "last_shift": None},
            {"name": "Служител 3", "start_date": "2025-01-01", "last_shift": None},
            {"name": "Служител 4", "start_date": "2025-01-01", "last_shift": None},
        ],
        "admin": {
            "name": "Администратор",
            "start_date": "2025-01-01"
        }
    }


@pytest.fixture
def empty_last_month():
    return None


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weight_department_schedule.settings")
django.setup()


