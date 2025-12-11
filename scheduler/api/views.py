import calendar
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from scheduler.models import MonthRecord, Employee
from scheduler.logic.generator.generator import generate_new_month
from scheduler.logic.months_logic import load_month, save_month
from scheduler.logic.generator.apply_overrides import apply_overrides

from scheduler.api.errors import api_error
from scheduler.api.serializers import (
    OverrideSerializer,
    GenerateMonthSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer
)

from scheduler.api.utils.holidays import get_holidays_for_month


class MonthInfoView(APIView):
    def get(self, request, year, month):
        year = int(year)
        month = int(month)

        days_count = calendar.monthrange(year, month)[1]

        weekends = []
        for d in range(1, days_count + 1):
            wd = calendar.weekday(year, month, d)
            if wd in (5, 6):
                weekends.append(d)

        holidays = get_holidays_for_month(year, month)

        return Response({
            "year": year,
            "month": month,
            "days": days_count,
            "weekends": weekends,
            "holidays": holidays,
        })


class ScheduleView(APIView):
    def get(self, request, year, month):
        try:
            data = load_month(year, month)
        except FileNotFoundError:
            return api_error(
                code="NOT_FOUND",
                message="Месецът не съществува.",
                hint="Генерирайте го чрез /api/generate-month/.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)


class GenerateMonthView(APIView):
    def post(self, request):
        serializer = GenerateMonthSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни параметри за генериране на месец.",
                hint=str(serializer.errors)
            )

        data = serializer.validated_data
        year = data['year']
        month = data['month']


        generated = generate_new_month(year, month)


        save_month(year, month, generated)


        return Response({
            "year": year,
            "month": month,
            "generated": True,
            "data": generated
        }, status=status.HTTP_201_CREATED)



class EmployeeListCreateView(APIView):
    def get(self, request):
        employees = Employee.objects.all().order_by('full_name')
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)

        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни данни за създаване на служител.",
                hint=str(serializer.errors)
            )

        employee = serializer.save()
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)


class EmployeeDetailView(APIView):
    def put(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Служителят не е намерен.",
                hint="Проверете дали ID-то е валидно.",
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

        for field, value in data.items():
            setattr(employee, field, value)

        employee.save()
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_200_OK)

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


class ScheduleOverrideAPI(APIView):
    def post(self, request, year, month):
        employee_id = str(request.data["employee_id"])
        day = str(request.data["day"])
        shift = request.data["shift"]

        data = load_month(year, month)

        if "overrides" not in data:
            data["overrides"] = {}

        if employee_id not in data["overrides"]:
            data["overrides"][employee_id] = {}

        data["overrides"][employee_id][day] = shift

        data["schedule"] = apply_overrides(
            data["schedule"],
            data["overrides"]
        )

        save_month(year, month, data)

        return Response({"status": "ok", "applied": True})



