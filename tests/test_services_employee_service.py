import pytest
import uuid
from scheduler.models import Employee
from scheduler.services.employee_service import EmployeeService


def uname():
    return f"User-{uuid.uuid4()}"


@pytest.mark.django_db
def test_get_active_employees_for_month():
    e1 = Employee.objects.create(
        full_name=uname(),
        start_date="2024-01-01",
        is_active=True,
    )


    e2 = Employee.objects.create(
        full_name=uname(),
        start_date="2024-06-01",
        is_active=True,
    )


    e3 = Employee.objects.create(
        full_name=uname(),
        start_date="2023-01-01",
        end_date="2024-02-01",
        is_active=True,
    )

    result = EmployeeService.get_active_employees_for_month(2024, 3)

    assert e1.full_name in result
    assert e2.full_name not in result
    assert e3.full_name not in result


@pytest.mark.django_db
def test_get_all_employees():
    e1 = Employee.objects.create(full_name=uname(), is_active=True)
    e2 = Employee.objects.create(full_name=uname(), is_active=False)
    e3 = Employee.objects.create(full_name=uname(), is_active=True)

    result = EmployeeService.get_all_employees()

    assert e1.full_name in result
    assert e3.full_name in result
    assert e2.full_name not in result
