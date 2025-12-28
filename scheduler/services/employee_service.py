from datetime import date
from scheduler.models import Employee


class EmployeeService:

    @staticmethod
    def get_active_employees_for_month(year, month):
        """
            Returns a list with names, that the generator can use.
        """

        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)

        employees = Employee.objects.filter(is_active=True)

        filtered = []
        for emp in employees:
            if emp.start_date and emp.start_date >= month_end:
                continue

            if emp.end_date and emp.end_date < month_start:
                continue

            filtered.append(emp.full_name)

        return filtered


    @staticmethod
    def get_all_employees():
        return list(Employee.objects.filter(is_active=True).values_list("full_name", flat=True))

