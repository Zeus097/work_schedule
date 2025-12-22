import calendar
from datetime import date

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from scheduler.logic.cycle_state import load_last_cycle_state, save_last_cycle_state
from scheduler.logic.generator.generator import generate_new_month
from scheduler.logic.months_logic import load_month, save_month, list_month_files
from scheduler.logic.generator.apply_overrides import apply_overrides
from scheduler.api.errors import api_error
from scheduler.api.serializers import (
    GenerateMonthSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
)
from scheduler.api.utils.holidays import get_holidays_for_month
from scheduler.models import AdminEmployee, Employee


def _prev_year_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _normalize_shift(s):
    return str(s).strip() if s else ""


class MonthInfoView(APIView):
    def get(self, request, year, month):
        days = calendar.monthrange(year, month)[1]
        weekends = [d for d in range(1, days + 1) if calendar.weekday(year, month, d) >= 5]
        holidays = get_holidays_for_month(year, month)

        return Response({
            "year": year,
            "month": month,
            "days": days,
            "weekends": weekends,
            "holidays": holidays
        })


class ScheduleView(APIView):
    def get(self, request, year, month):
        try:
            data = load_month(year, month)
        except FileNotFoundError:
            return api_error("NOT_FOUND", "Месецът не съществува.", http_status=404)

        days = calendar.monthrange(year, month)[1]
        employees = Employee.objects.all()

        schedule = data.get("schedule", {})
        overrides = data.get("overrides", {})

        rebuilt = {}
        for emp in employees:
            eid = str(emp.id)
            rebuilt[eid] = schedule.get(eid) or {str(d): "" for d in range(1, days + 1)}

        data["schedule"] = rebuilt
        data["overrides"] = {k: v for k, v in overrides.items() if k in rebuilt}
        save_month(year, month, data)

        final_schedule = apply_overrides(data["schedule"], data["overrides"])

        return Response({
            "year": year,
            "month": month,
            "schedule": final_schedule,
            "overrides": data["overrides"],
            "generator_locked": bool(data.get("generator_locked")),
            "ui_locked": bool(data.get("ui_locked")),
        })


class GenerateMonthView(APIView):
    def post(self, request):
        serializer = GenerateMonthSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                "INVALID_INPUT",
                "Невалидни параметри.",
                http_status=400
            )

        year = serializer.validated_data["year"]
        month = serializer.validated_data["month"]

        first_run = not load_last_cycle_state() and not list_month_files()

        if not first_run:
            py, pm = _prev_year_month(year, month)
            try:
                prev = load_month(py, pm)
                if not prev.get("ui_locked"):
                    return api_error(
                        "PREV_NOT_LOCKED",
                        "Предходният месец не е заключен.",
                        http_status=409
                    )
            except FileNotFoundError:
                return api_error(
                    "PREV_MISSING",
                    "Липсва предходният месец.",
                    http_status=409
                )


        try:
            generated = generate_new_month(year, month)
        except Exception:
            raise


        generated["ui_locked"] = False
        save_month(year, month, generated)

        return Response(
            {
                "generated": True,
                "bootstrap": first_run
            },
            status=201
        )




class ScheduleOverrideAPI(APIView):
    def post(self, request, year, month):
        emp_id = str(request.data.get("employee_id"))
        day = str(request.data.get("day"))
        shift = _normalize_shift(request.data.get("new_shift"))

        data = load_month(year, month)
        if data.get("ui_locked"):
            return Response({"error": "Месецът е заключен."}, status=409)

        data.setdefault("schedule", {}).setdefault(emp_id, {})[day] = shift
        data.setdefault("overrides", {}).setdefault(emp_id, {})[day] = shift
        save_month(year, month, data)

        return Response({"status": "ok"})


class LockMonthView(APIView):
    def post(self, request, year, month):
        data = load_month(year, month)

        if data.get("ui_locked"):
            return Response({"error": "Вече заключен."}, status=409)

        data["schedule"] = apply_overrides(data.get("schedule", {}), data.get("overrides", {}))
        data["ui_locked"] = True
        save_month(year, month, data)

        last_day = calendar.monthrange(year, month)[1]
        save_last_cycle_state(data["schedule"], date(year, month, last_day))

        return Response({"status": "locked"})


@method_decorator(csrf_exempt, name="dispatch")
class SetAdminView(APIView):
    def post(self, request):
        eid = request.data.get("employee_id")
        employee = Employee.objects.get(id=eid)

        AdminEmployee.objects.all().delete()
        AdminEmployee.objects.create(employee=employee)

        return Response({"status": "ok"})


class EmployeeListCreateView(APIView):
    def get(self, request):
        employees = Employee.objects.all().order_by("full_name")
        return Response(
            EmployeeSerializer(employees, many=True).data
        )

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни данни.",
                hint=str(serializer.errors),
                http_status=status.HTTP_400_BAD_REQUEST
            )

        employee = serializer.save()
        return Response(
            EmployeeSerializer(employee).data,
            status=status.HTTP_201_CREATED
        )



class EmployeeDetailView(APIView):
    def put(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Служителят не е намерен.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни данни.",
                hint=str(serializer.errors),
                http_status=status.HTTP_400_BAD_REQUEST
            )

        for key, value in serializer.validated_data.items():
            setattr(employee, key, value)
        employee.save()

        return Response(EmployeeSerializer(employee).data)

    def delete(self, request, id):
        try:
            Employee.objects.get(id=id).delete()
        except Employee.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Служителят не е намерен.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)



