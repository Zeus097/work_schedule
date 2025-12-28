import sys
import types
from pathlib import Path
from unittest.mock import patch


def setup_fake_django_settings(tmp_path):
    fake = types.ModuleType("fake_settings")
    fake.BASE_DIR = str(tmp_path)
    sys.modules["fake_settings"] = fake
    return fake


def test_get_month_path(tmp_path, monkeypatch):
    setup_fake_django_settings(tmp_path)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "fake_settings")

    from scheduler.logic.months_logic import get_month_path
    p = get_month_path(2026, 1)

    assert isinstance(p, Path)
    assert str(p).endswith("1.json")


def test_get_latest_month(tmp_path, monkeypatch):
    setup_fake_django_settings(tmp_path)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "fake_settings")

    data_dir = Path(tmp_path) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "1.json").write_text('{"a":1}')
    (data_dir / "2026-03.json").write_text('{"b":2}')

    with patch("scheduler.logic.months_logic.DATA_DIR", data_dir):
        from scheduler.logic.months_logic import get_latest_month
        year, month, data = get_latest_month()

    assert year == 2026
    assert month == 3
    assert data == {"b": 2}


