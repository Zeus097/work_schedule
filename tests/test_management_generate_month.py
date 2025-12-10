import pytest
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from scheduler.models import Employee, MonthRecord

FAKE_CONFIG = {
    "employees": [{"name": "TestUser"}],
    "admin": {"name": "AdminUser"},
}

def unique():
    import uuid
    return "User_" + uuid.uuid4().hex[:8]


@pytest.mark.django_db
def test_generate_month_success(monkeypatch):
    monkeypatch.setattr(
        "scheduler.logic.json_help_functions.load_json_file",
        lambda name: FAKE_CONFIG.copy()
    )

    saved_cfg = {}
    def fake_write(data, name):
        saved_cfg["cfg"] = data

    monkeypatch.setattr(
        "scheduler.logic.json_help_functions.write_json_file",
        fake_write
    )

    Employee.objects.create(full_name=unique())
    Employee.objects.create(full_name=unique())

    out = StringIO()
    call_command("generate_month", 2030, 5, stdout=out)

    assert MonthRecord.objects.filter(year=2030, month=5).exists()
    assert "Графикът е записан успешно" in out.getvalue()


@pytest.mark.django_db
def test_generate_month_no_employees(monkeypatch):
    monkeypatch.setattr(
        "scheduler.services.employee_service.EmployeeService.get_active_employees_for_month",
        lambda y, m: []
    )

    monkeypatch.setattr(
        "scheduler.logic.json_help_functions.load_json_file",
        lambda name: {"employees": [], "admin": {"name": "X"}}
    )

    with pytest.raises(CommandError):
        call_command("generate_month", 2030, 5)


@pytest.mark.django_db
def test_generate_month_updates_existing(monkeypatch):
    monkeypatch.setattr(
        "scheduler.logic.json_help_functions.load_json_file",
        lambda name: FAKE_CONFIG.copy()
    )

    out = StringIO()

    # FIX: use update_or_create → NO UNIQUE ERROR
    MonthRecord.objects.update_or_create(
        year=2032,
        month=2,
        defaults={"data": {"old": True}}
    )

    Employee.objects.create(full_name=unique())

    call_command("generate_month", 2032, 2, stdout=out)

    rec = MonthRecord.objects.get(year=2032, month=2)
    assert rec.data is not None
