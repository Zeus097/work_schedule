import calendar
from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from scheduler.logic.cycle_state import load_last_cycle_state, save_last_cycle_state
from scheduler.logic.generator.generator import generate_new_month
from scheduler.logic.json_help_functions import _load_json
from scheduler.logic.months_logic import list_month_files, get_month_path
from scheduler.logic.generator.apply_overrides import apply_overrides
from scheduler.api.serializers import (
    GenerateMonthSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
)
from scheduler.api.utils.holidays import get_holidays_for_month
from scheduler.logic.validators.validators import validate_month
from scheduler.models import Employee, MonthAdmin
from scheduler.api.utils.validation_errors import humanize_validation_error
from scheduler.logic.months_logic import load_month, save_month
from scheduler.api.errors import api_error
from scheduler.logic.cycle_state_extractor import extract_cycle_state_from_schedule




def _prev_year_month(year: int, month: int) -> tuple[int, int]:
    """
        Returns the previous year and month pair.
        Handles year rollover when the current month is January.
    """

    return (year - 1, 12) if month == 1 else (year, month - 1)


def _normalize_shift(s):
    """
        Normalizes a shift value to a clean string.
        Converts the input to a stripped string or returns an empty
        string for falsy values.
    """

    return str(s).strip() if s else ""


class MonthInfoView(APIView):
    """
        API endpoint providing basic calendar information for a month.
        Returns the number of days, weekend dates, and official holidays
        for the specified year and month.
    """

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
    """
        Read-only normalization view.
        NEVER modifies ui_locked.
    """

    def get(self, request, year, month):
        try:
            data = load_month(year, month)
        except FileNotFoundError:
            return Response({
                "year": year,
                "month": month,
                "schedule": {},
                "overrides": {},
                "generator_locked": False,
                "ui_locked": False,
                "is_new": True,
            })

        days = calendar.monthrange(year, month)[1]
        employees = Employee.objects.all()

        schedule = data.get("schedule", {})
        overrides = data.get("overrides", {})
        ui_locked = bool(data.get("ui_locked", False))
        generator_locked = bool(data.get("generator_locked", False))

        rebuilt = {}

        for emp in employees:
            eid = str(emp.id)
            emp_days = schedule.get(eid, {})

            rebuilt[eid] = {
                str(d): emp_days.get(str(d), "")
                for d in range(1, days + 1)
            }

        data["schedule"] = rebuilt
        data["overrides"] = {
            emp_id: {
                str(day): shift
                for day, shift in days_map.items()
                if str(day) in rebuilt.get(emp_id, {})
            }
            for emp_id, days_map in overrides.items()
            if emp_id in rebuilt
        }

        data["ui_locked"] = ui_locked
        data["generator_locked"] = generator_locked

        save_month(year, month, data)

        final_schedule = apply_overrides(
            data["schedule"],
            data["overrides"]
        )

        return Response({
            "year": year,
            "month": month,
            "schedule": final_schedule,
            "overrides": data["overrides"],
            "generator_locked": generator_locked,
            "ui_locked": ui_locked,
            "month_admin_id": data.get("month_admin_id"),
        })


class GenerateMonthView(APIView):
    def _freeze_month(self, year: int, month: int, reason: str):
        data = {
            "year": year,
            "month": month,
            "schedule": {},
            "overrides": {},
            "ui_locked": False,
            "generator_locked": True,
            "freeze_reason": reason,
        }
        save_month(year, month, data)


    @staticmethod
    def _is_empty_schedule(schedule: dict) -> bool:
        return all(
            all(v == "" for v in days.values())
            for days in schedule.values()
        )


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
        strict = serializer.validated_data.get("strict", True)

        employees_count = Employee.objects.filter(is_active=True).count()
        try:
            data = load_month(year, month)
            admin_exists = bool(data.get("month_admin_id"))
        except FileNotFoundError:
            admin_exists = False

        if employees_count < 4:
            self._freeze_month(year, month, "MIN_EMPLOYEES")
            return Response({"generated": False, "frozen": True}, status=200)

        if not admin_exists:
            self._freeze_month(year, month, "NO_ADMIN")
            return Response({"generated": False, "frozen": True}, status=200)

        first_run = not load_last_cycle_state() and not list_month_files()

        try:
            existing = load_month(year, month)

            if self._is_empty_schedule(existing.get("schedule", {})):
                strict = False

            if not existing.get("ui_locked"):
                employees = {
                    str(e.id): e.name
                    for e in Employee.objects.filter(is_active=True)
                }

                generated = generate_new_month(
                    year=year,
                    month=month,
                    employees=employees,
                    strict=strict,
                )

                generated["ui_locked"] = False
                save_month(year, month, generated)

                return Response(
                    {
                        "generated": True,
                        "warnings": generated.get("warnings", []),
                        "regenerated": True,
                        "strict": strict,
                    },
                    status=201
                )

        except FileNotFoundError:
            pass

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
                strict = False
            except FileNotFoundError:
                return api_error(
                    "PREV_MISSING",
                    "Липсва предходният месец.",
                    http_status=409
                )

        employees = {
            str(e.id): e.name
            for e in Employee.objects.filter(is_active=True)
        }

        try:
            generated = generate_new_month(
                year=year,
                month=month,
                employees=employees,
                strict=strict,
            )
        except Exception:
            return api_error(
                "GENERATOR_ERROR",
                "Възникна вътрешна грешка при генериране на графика.\n"
                "Моля, опитайте отново или се свържете с администратора.",
                http_status=409
            )

        generated["ui_locked"] = False
        save_month(year, month, generated)

        return Response(
            {
                "generated": True,
                "warnings": generated.get("warnings", []),
                "bootstrap": first_run,
                "strict": strict,
            },
            status=201
        )


class ScheduleOverrideAPI(APIView):
    """
        API endpoint for applying manual schedule overrides.
        Allows updating a single employee’s shift for a specific day,
        persists the override, and blocks modifications if the month is locked.
    """

    def post(self, request, year, month):
        emp_id = str(request.data.get("employee_id"))
        day = int(request.data.get("day"))
        shift = _normalize_shift(request.data.get("new_shift"))

        data = load_month(year, month)

        if data.get("ui_locked"):
            return api_error(
                "MONTH_LOCKED",
                "Месецът е заключен.",
                http_status=409
            )

        data.setdefault("schedule", {}).setdefault(emp_id, {})[day] = shift
        data.setdefault("overrides", {}).setdefault(emp_id, {})[day] = shift

        save_month(year, month, data)

        return Response({"status": "ok"})


class LockMonthView(APIView):
    """
        Validates and permanently locks a monthly schedule.
    """

    def post(self, request, year, month):
        path = get_month_path(year, month)

        try:
            data = _load_json(path)
        except FileNotFoundError:
            return api_error(
                "NOT_FOUND",
                "Месецът не съществува.",
                http_status=404
            )

        if data.get("ui_locked") is True:
            return api_error(
                "ALREADY_LOCKED",
                "Месецът вече е заключен.",
                http_status=409
            )

        schedule = data.get("schedule", {})
        overrides = data.get("overrides", {})

        final_schedule = apply_overrides(schedule, overrides)

        days = calendar.monthrange(year, month)[1]
        weekdays = {
            d: calendar.weekday(year, month, d)
            for d in range(1, days + 1)
        }

        admin_id = data.get("month_admin_id")

        errors = validate_month(
            final_schedule,
            crisis_mode=False,
            weekdays=weekdays,
            admin_id=str(admin_id),
        )

        if errors:
            readable = [
                humanize_validation_error(emp, day, msg, error_type)
                for emp, day, msg, error_type in errors
            ]

            blocking = [
                e for e in readable
                if e.get("type") == "blocking"
            ]

            if blocking:
                return Response(
                    {
                        "ok": False,
                        "locked": False,
                        "errors": blocking,
                        "message": "Месецът има блокиращи грешки."
                    },
                    status=409
                )

        data["schedule"] = final_schedule
        data["ui_locked"] = True

        save_month(year, month, data)

        return Response(
            {
                "ok": True,
                "locked": True,
                "year": year,
                "month": month
            },
            status=200
        )


class EmployeeListCreateView(APIView):
    """
        API endpoint for listing and creating employees.
        Supports retrieving all employees ordered by name and
        creating new employee records with input validation.
    """

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
    """
        API endpoint for updating and deleting a single employee.
        Handles employee modification with validation and supports
        safe deletion, returning appropriate errors when the employee
        does not exist.
    """

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


class ValidateMonthView(APIView):
    """
        API endpoint for validating a monthly schedule without locking it.
        Loads the stored month data, runs schedule validation against
        business rules, and returns whether the schedule is valid
        along with any detected errors.
    """

    def post(self, request, year, month):
        data = load_month(year, month)
        try:
            admin = MonthAdmin.objects.get(year=year, month=month)
        except MonthAdmin.DoesNotExist:
            return Response(
                {"valid": False, "errors": ["Няма избран администратор."]},
                status=400
            )

        admin_id = str(admin.employee.id)

        errors = validate_month(data["schedule"], admin_id)

        return Response({
            "valid": len(errors) == 0,
            "errors": errors,
        })


class ClearScheduleAPI(APIView):
    """
        API endpoint for clearing a monthly schedule.
        Removes all shifts and overrides for an unlocked month,
        resets its state, and persists the cleared data.
    """

    def post(self, request, year: int, month: int):
        data = load_month(year, month)

        if not data:
            return api_error(
                code="MONTH_NOT_FOUND",
                message="Месецът не съществува.",
                http_status=404,
            )

        if data.get("ui_locked"):
            return api_error(
                code="MONTH_LOCKED",
                message="Месецът е заключен и не може да се изчисти.",
                http_status=409,
            )

        data["schedule"] = {}
        data["overrides"] = {}
        data["ui_locked"] = False
        save_month(year, month, data)
        return Response({"ok": True})


class ClearMonthScheduleAPI(APIView):
    """
        API endpoint for fully resetting a month's schedule state.
        Clears all shifts, overrides, and related scheduling metadata
        for an unlocked month, effectively returning it to a clean state.
    """

    def post(self, request, year: int, month: int):
        data = load_month(year, month)

        if data.get("ui_locked"):
            return api_error(
                code="MONTH_LOCKED",
                message="Месецът е заключен.",
                hint="Отключи месеца или използвай 'Приеми като начало'.",
                http_status=409
            )

        data["schedule"] = {}
        data["overrides"] = {}
        data["states"] = {}
        data["ideal"] = {}
        save_month(year, month, data)
        return Response({"status": "ok"})


class AcceptMonthAsStartAPI(APIView):
    def post(self, request, year: int, month: int):
        data = load_month(year, month)

        if not data.get("schedule"):
            return api_error(
                code="EMPTY_MONTH",
                message="Месецът няма график.",
                http_status=400
            )

        admin_id = data.get("month_admin_id")
        if not admin_id:
            return api_error(
                code="NO_ADMIN",
                message="Няма избран администратор.",
                http_status=400
            )

        final_schedule = apply_overrides(
            data.get("schedule", {}),
            data.get("overrides", {})
        )

        last_day_num = calendar.monthrange(year, month)[1]
        last_day_date = date(year, month, last_day_num)

        from scheduler.logic.generator.generator import CYCLE, CYCLE_LEN

        state = {}

        for emp_id, days in final_schedule.items():
            if str(emp_id) == str(admin_id):
                continue

            last_shift = None
            for day in sorted(days.keys(), key=int):
                if days[day] in ("Д", "Н", "В"):
                    last_shift = days[day]

            if last_shift is None:
                cycle_index = 0
            else:
                cycle_index = max(
                    i for i, s in enumerate(CYCLE) if s == last_shift
                ) + 1

            state[str(emp_id)] = {
                "cycle_index": cycle_index % CYCLE_LEN
            }

        save_last_cycle_state(state, last_day_date)

        return Response({"ok": True})


class SetMonthAdminView(APIView):
    def post(self, request, year: int, month: int):
        emp_id = str(request.data.get("employee_id"))

        if not Employee.objects.filter(id=emp_id).exists():
            return api_error(
                code="EMP_NOT_FOUND",
                message="Служителят не съществува.",
                http_status=404
            )

        try:
            data = load_month(year, month)
        except FileNotFoundError:
            data = {
                "year": year,
                "month": month,
                "schedule": {},
                "overrides": {},
                "ui_locked": False,
                "generator_locked": False,
            }

        if data.get("ui_locked"):
            return api_error(
                code="MONTH_LOCKED",
                message="Месецът е заключен.",
                http_status=409
            )

        data["month_admin_id"] = emp_id
        save_month(year, month, data)

        return Response({"ok": True})



