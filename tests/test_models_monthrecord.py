import pytest
from scheduler.models import MonthRecord


@pytest.mark.django_db
def test_monthrecord_creation():
    data = {"schedule": {}, "meta": {"src": "test"}}

    record = MonthRecord.objects.create(year=2099, month=12, data=data)

    assert record.id is not None
    assert record.year == 2099
    assert record.month == 12
    assert record.data["meta"]["src"] == "test"


@pytest.mark.django_db
def test_monthrecord_unique_constraint():
    MonthRecord.objects.create(year=2098, month=11, data={})

    with pytest.raises(Exception):
        MonthRecord.objects.create(year=2098, month=11, data={})
