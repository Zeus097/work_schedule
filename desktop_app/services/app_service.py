import calendar
from desktop_app.utils.holidays import get_holidays_for_month
from scheduler.logic.generator.generator import generate_new_month
from scheduler.logic.months_logic import load_month, save_month
from scheduler.logic.validators.validators import validate_month
from scheduler.storage.json_storage import (
    clear_month_data,
    load_employees,
    save_employees,
)





class AppService:
    def get_schedule(self, year: int, month: int):
        data = load_month(year, month)
        if not data:
            raise FileNotFoundError

        raw = data.get("schedule", {})
        data["schedule"] = {
            emp: {int(day): shift for day, shift in days.items()}
            for emp, days in raw.items()
        }
        return data


    def get_employees(self):
        return load_employees()


    def get_month_info(self, year: int, month: int):
        days_in_month = calendar.monthrange(year, month)[1]

        weekends = [
            day
            for day in range(1, days_in_month + 1)
            if calendar.weekday(year, month, day) >= 5
        ]

        holidays = get_holidays_for_month(year, month)

        return {
            "days": days_in_month,
            "weekends": weekends,
            "holidays": holidays,
        }


    def generate_month(self, year: int, month: int, strict: bool = True):
        raw_employees = load_employees()

        employees = {
            str(e["id"]): e["full_name"]
            for e in raw_employees
            if e.get("is_active")
        }

        result = generate_new_month(year, month, employees, strict)

        save_month(year, month, result)
        return result


    def clear_month(self, year: int, month: int):
        clear_month_data(year, month)
        return {"ok": True}


    def get_month_admin(self, year: int, month: int):
        try:
            data = load_month(year, month)
            return data.get("month_admin_id")
        except FileNotFoundError:
            return None


    def add_employee(self, data: dict):
        employees = load_employees()

        next_id = (
                max((int(e.get("id", 0)) for e in employees), default=0) + 1
        )

        employee = {
            "id": next_id,
            "full_name": data.get("full_name", "").strip(),
            "card_number": (data.get("card_number") or "").strip(),
            "is_active": True,
        }

        employees.append(employee)
        save_employees(employees)


    def update_employee(self, emp_id: int | str, data: dict):
        employees = load_employees()
        emp_id = str(emp_id)

        for e in employees:
            if str(e.get("id")) == emp_id:
                e["full_name"] = data.get("full_name", e.get("full_name"))
                e["card_number"] = data.get("card_number", e.get("card_number"))
                e["is_active"] = data.get("is_active", e.get("is_active", True))
                break

        save_employees(employees)


    def delete_employee(self, emp_id: int | str):
        emp_id = str(emp_id)
        employees = [
            e for e in load_employees()
            if str(e.get("id")) != emp_id
        ]
        save_employees(employees)


    def set_month_admin(self, year: int, month: int, admin_id: int | str):
        try:
            data = load_month(year, month)
        except FileNotFoundError:
            data = {
                "year": year,
                "month": month,
                "schedule": {},
                "overrides": {},
                "generator_locked": False,
                "ui_locked": False,
            }

        data["month_admin_id"] = str(admin_id)
        save_month(year, month, data)
        return {"ok": True}


    def post_override(self, year: int, month: int, data: dict):
        month_data = load_month(year, month)

        overrides = month_data.setdefault("overrides", {})

        emp_id = str(data["employee_id"])
        day = str(data["day"])
        shift = data.get("new_shift", "")

        overrides.setdefault(emp_id, {})[day] = shift

        save_month(year, month, month_data)

        return {"ok": True}


    def lock_month(self, year: int, month: int):
        data = load_month(year, month)

        schedule = data.get("schedule", {})
        admin_id = data.get("month_admin_id")

        if not admin_id:
            return {
                "ok": False,
                "message": "Няма избран администратор."
            }

        days_in_month = calendar.monthrange(year, month)[1]
        weekdays = {
            day: calendar.weekday(year, month, day)
            for day in range(1, days_in_month + 1)
        }

        errors = validate_month(
            schedule=schedule,
            crisis_mode=False,
            weekdays=weekdays,
            admin_id=admin_id,
        )

        blocking = [e for e in errors if e[3] == "blocking"]
        if blocking:
            return {
                "ok": False,
                "errors": errors,
            }

        data["ui_locked"] = True
        save_month(year, month, data)

        return {"ok": True}
