import sys
import types
from pathlib import Path
from unittest.mock import patch
import importlib


def setup_fake_django_settings(tmp_path):
    fake = types.ModuleType("fake_settings")
    fake.BASE_DIR = str(tmp_path)
    sys.modules["fake_settings"] = fake


def reload_months_logic_with_data_dir(data_dir):

    if "scheduler.logic.months_logic" in sys.modules:
        del sys.modules["scheduler.logic.months_logic"]

    with patch("scheduler.logic.file_paths.DATA_DIR", data_dir):
        import scheduler.logic.months_logic as ml
        importlib.reload(ml)
        return ml


def test_get_month_path(tmp_path, monkeypatch):
    setup_fake_django_settings(tmp_path)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "fake_settings")

    data_dir = Path(tmp_path) / "data"
    data_dir.mkdir()

    ml = reload_months_logic_with_data_dir(data_dir)

    p = ml.get_month_path(2026, 1)
    assert str(p).endswith("2026-01.json")


def test_save_and_load_month(tmp_path, monkeypatch):
    setup_fake_django_settings(tmp_path)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "fake_settings")

    data_dir = Path(tmp_path) / "data"
    data_dir.mkdir()

    ml = reload_months_logic_with_data_dir(data_dir)

    data = {"a": 1}
    ml.save_month(2026, 2, data)

    loaded = ml.load_month(2026, 2)
    assert loaded == data


def test_list_month_files(tmp_path, monkeypatch):
    setup_fake_django_settings(tmp_path)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "fake_settings")

    data_dir = Path(tmp_path) / "data"
    data_dir.mkdir()

    (data_dir / "2026-01.json").write_text("{}")
    (data_dir / "2026-02.json").write_text("{}")
    (data_dir / "ignore.txt").write_text("x")

    ml = reload_months_logic_with_data_dir(data_dir)

    result = ml.list_month_files()

    assert len(result) == 2
    assert result[0][1] == 1
    assert result[1][1] == 2


def test_get_latest_month(tmp_path, monkeypatch):
    setup_fake_django_settings(tmp_path)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "fake_settings")

    data_dir = Path(tmp_path) / "data"
    data_dir.mkdir()

    (data_dir / "2026-01.json").write_text('{"a":1}')
    (data_dir / "2026-03.json").write_text('{"b":2}')

    ml = reload_months_logic_with_data_dir(data_dir)

    y, m, data = ml.get_latest_month()

    assert y == 2026
    assert m == 3
    assert data == {"b": 2}



