import calendar
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from scheduler.models import Employee
from scheduler.logic.generator.generator import generate_new_month
from scheduler.logic.months_logic import load_month, save_month, get_latest_month
from scheduler.logic.generator.apply_overrides import apply_overrides

from scheduler.api.errors import api_error
from scheduler.api.serializers import (
    GenerateMonthSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
)
from scheduler.api.utils.holidays import get_holidays_for_month


class MonthInfoView(APIView):
    def get(self, request, year, month):
        days_count = calendar.monthrange(year, month)[1]
        weekends = [d for d in range(1, days_count + 1)
                    if calendar.weekday(year, month, d) in (5, 6)]
        holidays = get_holidays_for_month(year, month)

        return Response({
            "year": year,
            "month": month,
            "days": days_count,
            "weekends": weekends,
            "holidays": holidays
        })


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

        return Response({
            "schedule": data["schedule"],
            "overrides": data.get("overrides", {}),
        })


class GenerateMonthView(APIView):
    def post(self, request):
        serializer = GenerateMonthSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни параметри.",
                hint=str(serializer.errors),
                http_status=status.HTTP_400_BAD_REQUEST
            )

        year = serializer.validated_data["year"]
        month = serializer.validated_data["month"]

        # 1) Проверка: има ли вече файл за месеца
        try:
            existing = load_month(year, month)
            # ако има файл → проверяваме lock
            if existing.get("generator_locked", False):
                return api_error(
                    code="MONTH_LOCKED",
                    message="Месецът е заключен за повторно генериране.",
                    hint="Може да се редактира ръчно, но не и да се генерира наново.",
                    http_status=status.HTTP_409_CONFLICT
                )

            # ако има файл, но не е заключен – пак не позволяваме регенерация
            return api_error(
                code="MONTH_ALREADY_EXISTS",
                message="Месецът вече съществува.",
                hint="Използвайте ръчни корекции (override).",
                http_status=status.HTTP_409_CONFLICT
            )

        except FileNotFoundError:
            # файлът НЕ съществува → продължаваме към генериране
            pass

        # 2) Генериране
        try:
            generated = generate_new_month(
                year=year,
                month=month
            )
        except Exception as e:
            return api_error(
                code="GENERATOR_ERROR",
                message="Грешка при генериране на месец.",
                hint=str(e),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3) Добавяме generator lock по подразбиране
        generated["generator_locked"] = True

        save_month(year, month, generated)

        return Response(
            {
                "year": year,
                "month": month,
                "generated": True,
                "data": generated,
            },
            status=status.HTTP_201_CREATED,
        )




class EmployeeListCreateView(APIView):
    def get(self, request):
        employees = Employee.objects.all().order_by("full_name")
        return Response(EmployeeSerializer(employees, many=True).data)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни данни.",
                hint=str(serializer.errors)
            )
        employee = serializer.save()
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)


class EmployeeDetailView(APIView):
    def put(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return api_error("NOT_FOUND", "Служителят не е намерен.")

        serializer = EmployeeUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error("INVALID_INPUT", "Невалидни данни.", str(serializer.errors))

        for key, value in serializer.validated_data.items():
            setattr(employee, key, value)
        employee.save()

        return Response(EmployeeSerializer(employee).data)

    def delete(self, request, id):
        try:
            Employee.objects.get(id=id).delete()
        except Employee.DoesNotExist:
            return api_error("NOT_FOUND", "Служителят не е намерен.")
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScheduleOverrideAPI(APIView):
    def post(self, request, year, month):
        employee_id = str(request.data.get("employee_id"))
        day = str(request.data.get("day"))
        shift = request.data.get("new_shift")

        data = load_month(year, month)
        data.setdefault("overrides", {})
        data["overrides"].setdefault(employee_id, {})
        data["overrides"][employee_id][day] = shift

        data["schedule"] = apply_overrides(data["schedule"], data["overrides"])
        save_month(year, month, data)

        return Response({"status": "ok", "applied": True})








