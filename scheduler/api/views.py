import calendar
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from scheduler.models import Employee
from scheduler.logic.generator.generator import generate_new_month
from scheduler.logic.months_logic import load_month, save_month
from scheduler.logic.generator.apply_overrides import apply_overrides

from scheduler.api.errors import api_error
from scheduler.api.serializers import (
    GenerateMonthSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
)

from scheduler.api.utils.holidays import get_holidays_for_month


# ---------------------------------------------------------
# MONTH INFO
# ---------------------------------------------------------
class MonthInfoView(APIView):
    def get(self, request, year, month):
        year = int(year)
        month = int(month)

        days_count = calendar.monthrange(year, month)[1]

        weekends = [
            d for d in range(1, days_count + 1)
            if calendar.weekday(year, month, d) in (5, 6)
        ]

        holidays = get_holidays_for_month(year, month)

        return Response({
            "year": year,
            "month": month,
            "days": days_count,
            "weekends": weekends,
            "holidays": holidays
        })


# ---------------------------------------------------------
# SCHEDULE VIEW
# ---------------------------------------------------------
class ScheduleView(APIView):
    def get(self, request, year, month):
        try:
            data = load_month(year, month)
        except FileNotFoundError:
            return api_error(
                code="NOT_FOUND",
                message="Месецът не съществува.",
                hint="Генерирайте го чрез /api/schedule/generate/.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        raw_schedule = data["schedule"]
        overrides = data.get("overrides", {})


        schedule_by_id = {}
        for emp_id, days in raw_schedule.items():
            schedule_by_id[str(emp_id)] = days

        overrides_by_id = {}
        for emp_id, days in overrides.items():
            overrides_by_id[str(emp_id)] = days

        return Response({
            "schedule": schedule_by_id,
            "overrides": overrides_by_id,
        }, status=status.HTTP_200_OK)


# ---------------------------------------------------------
# GENERATE MONTH
# ---------------------------------------------------------
class GenerateMonthView(APIView):
    def post(self, request):
        serializer = GenerateMonthSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни параметри за генериране на месец.",
                hint=str(serializer.errors)
            )

        year = serializer.validated_data['year']
        month = serializer.validated_data['month']

        generated = generate_new_month(year, month)
        save_month(year, month, generated)

        return Response({
            "year": year,
            "month": month,
            "generated": True,
            "data": generated
        }, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------
# EMPLOYEES LIST / CREATE
# ---------------------------------------------------------
class EmployeeListCreateView(APIView):
    def get(self, request):
        employees = Employee.objects.all().order_by("full_name")
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)

        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни данни за служител.",
                hint=str(serializer.errors)
            )

        employee = serializer.save()
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------
# EMPLOYEE UPDATE / DELETE
# ---------------------------------------------------------
class EmployeeDetailView(APIView):
    def put(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Служителят не е намерен.",
                hint="Проверете ID-то.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни данни за редакция.",
                hint=str(serializer.errors)
            )

        data = serializer.validated_data
        for key, value in data.items():
            setattr(employee, key, value)
        employee.save()

        return Response(EmployeeSerializer(employee).data)

    def delete(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Служителят не е намерен.",
                hint="Проверете ID-то.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        employee.delete()
        return Response({"status": "deleted"}, status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------
# OVERRIDE SCHEDULE
# ---------------------------------------------------------
class ScheduleOverrideAPI(APIView):
    def post(self, request, year, month):

        employee_id = request.data.get("employee_id")
        day = str(request.data.get("day"))
        shift = request.data.get("new_shift")

        if employee_id is None:
            return api_error(
                code="MISSING_ID",
                message="Липсва employee_id.",
                http_status=status.HTTP_400_BAD_REQUEST
            )


        try:
            emp = Employee.objects.get(id=int(employee_id))
        except Employee.DoesNotExist:
            return api_error(
                code="INVALID_EMPLOYEE",
                message=f"Няма служител с ID={employee_id}.",
                http_status=status.HTTP_400_BAD_REQUEST
            )

        emp_id = str(emp.id)

        data = load_month(year, month)

        if "overrides" not in data:
            data["overrides"] = {}

        if emp_id not in data["overrides"]:
            data["overrides"][emp_id] = {}

        data["overrides"][emp_id][day] = shift


        data["schedule"] = apply_overrides(data["schedule"], data["overrides"])

        save_month(year, month, data)

        return Response({"status": "ok", "applied": True})




