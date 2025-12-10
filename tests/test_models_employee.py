import pytest
import uuid
from scheduler.models import Employee, AdminEmployee


def unique_name():
    return f"TestUser-{uuid.uuid4()}"


@pytest.mark.django_db
def test_employee_creation():
    emp = Employee.objects.create(full_name=unique_name())
    assert emp.id is not None
    assert emp.is_active is True


@pytest.mark.django_db
def test_employee_with_dates():
    emp = Employee.objects.create(
        full_name=unique_name(),
        start_date="2024-05-10",
        end_date="2024-06-01",
        is_active=False,
    )

    assert str(emp.start_date) == "2024-05-10"
    assert str(emp.end_date) == "2024-06-01"
    assert emp.is_active is False



@pytest.mark.django_db
def test_admin_employee_creation():
    emp = Employee.objects.create(full_name=unique_name())
    admin = AdminEmployee.objects.create(employee=emp)

    assert admin.employee.full_name == emp.full_name
    assert admin.is_super_admin is True
