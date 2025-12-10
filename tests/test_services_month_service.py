import pytest
import uuid
import os
import json
from scheduler.models import MonthRecord
from scheduler.services.month_service import MonthService


def umonth():
    """Generate unique year, month."""
    # keep month stable but year unique for each test

    return 3000 + uuid.uuid4().int % 500, 1  # year 3000–3500


@pytest.mark.django_db
def test_save_month_and_get_month():
    year, month = umonth()
    data = {"schedule": {"A": {"1": "Д"}}, "meta": {"src": "test"}}

    MonthService.save_month(year, month, data)
    result = MonthService.get_month(year, month)

    assert result == data


@pytest.mark.django_db
def test_save_modified_month():
    year, month = umonth()
    original = {"schedule": {"A": {"1": "Д"}}, "meta": {}}
    modified = {"schedule": {"A": {"1": "П"}}, "meta": {"edit": True}}

    MonthService.save_month(year, month, original)
    MonthService.save_modified_month(year, month, modified)

    record = MonthRecord.objects.get(year=year, month=month)
    assert record.data == modified


@pytest.mark.django_db
def test_apply_override_valid():
    data = {
        "schedule": {
            "Иван": {"1": "Д", "2": "В"}
        }
    }

    new = MonthService.apply_override(data, "Иван", 2, "Н")
    assert new["schedule"]["Иван"]["2"] == "Н"


@pytest.mark.django_db
def test_apply_override_invalid_employee():
    data = {
        "schedule": {
            "Иван": {"1": "Д"}
        }
    }

    with pytest.raises(ValueError):
        MonthService.apply_override(data, "НямаГо", 1, "П")


@pytest.mark.django_db
def test_apply_override_invalid_day():
    data = {
        "schedule": {
            "Иван": {"1": "Д"}
        }
    }

    with pytest.raises(ValueError):
        MonthService.apply_override(data, "Иван", 5, "П")


@pytest.mark.django_db
def test_get_latest_month_from_db():
    MonthRecord.objects.all().delete()

    # Create 2 known records
    MonthService.save_month(2030, 5, {"schedule": {}})
    MonthService.save_month(2031, 1, {"schedule": {"X": {}}})

    y, m, data = MonthService.get_latest_month()

    assert (y, m) == (2031, 1)
    assert data == {"schedule": {"X": {}}}


@pytest.mark.django_db
def test_get_latest_month_from_json(tmp_path, monkeypatch):
    # Ensure DB is empty → force fallback to JSON
    MonthRecord.objects.all().delete()

    # Redirect DATA_DIR to a temp folder
    monkeypatch.setattr(MonthService, "DATA_DIR", tmp_path)

    json_data = {"schedule": {"A": {}}}

    file = tmp_path / "2025-07.json"
    with open(file, "w", encoding="utf-8") as f:
        json.dump(json_data, f)

    y, m, loaded = MonthService.get_latest_month()

    assert (y, m) == (2025, 7)
    assert loaded == json_data

