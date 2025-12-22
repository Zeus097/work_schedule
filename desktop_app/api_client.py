import requests
from desktop_app.config import API_BASE_URL


class APIClient:
    def __init__(self):
        self.base = API_BASE_URL


    def get_years(self):
        r = requests.get(f"{self.base}/meta/years/")
        r.raise_for_status()
        return r.json()

    def get_month_info(self, year: int, month: int):
        r = requests.get(f"{self.base}/meta/month-info/{year}/{month}/")
        r.raise_for_status()
        return r.json()


    def get_schedule(self, year: int, month: int):
        r = requests.get(f"{self.base}/schedule/{year}/{month}/")
        if r.status_code == 404:
            raise FileNotFoundError
        r.raise_for_status()

        data = r.json()

        # normalize days -> int
        raw_schedule = data.get("schedule", {})
        normalized_schedule = {
            emp: {int(day): shift for day, shift in days.items()}
            for emp, days in raw_schedule.items()
        }
        data["schedule"] = normalized_schedule
        return data

    def generate_month(self, year: int, month: int):
        url = f"{self.base}/schedule/generate/"
        r = requests.post(url, json={"year": int(year), "month": int(month)})


        if r.status_code == 201:
            return r.json()


        if r.status_code == 409:
            try:
                data = r.json()
                message = data.get("message", "Не може да се генерира месец.")
                hint = data.get("hint", "")
            except Exception:
                message = "Не може да се генерира месец."
                hint = ""
            raise RuntimeError(f"{message}\n{hint}".strip())


        try:
            data = r.json()
            message = data.get("message", "Грешка при генериране на графика.")
        except Exception:
            message = "Грешка при генериране на графика."

        raise RuntimeError(message)

    def post_override(self, year, month, data):
        r = requests.post(
            f"{self.base}/schedule/{year}/{month}/override/",
            json=data
        )

        if r.status_code >= 400:
            try:
                payload = r.json()
                message = payload.get("message", "Невалидна корекция.")
                hint = payload.get("hint", "")
                raise RuntimeError(f"{message}\n{hint}")
            except Exception:
                raise RuntimeError("Невалидна корекция.")

        return r.json()

    def get_employees(self):
        r = requests.get(f"{self.base}/employees/")
        r.raise_for_status()
        return r.json()

    def create_employee(self, data: dict):
        """Основният метод – използва се от UI"""
        r = requests.post(f"{self.base}/employees/", json=data)
        r.raise_for_status()
        return r.json()

    def add_employee(self, data: dict):
        """Alias за backward compatibility"""
        return self.create_employee(data)

    def update_employee(self, emp_id: int, data: dict):
        r = requests.put(f"{self.base}/employees/{emp_id}/", json=data)
        r.raise_for_status()
        return r.json()

    def delete_employee(self, emp_id: int):
        r = requests.delete(f"{self.base}/employees/{emp_id}/")
        r.raise_for_status()
        return True


    def lock_month(self, year: int, month: int, last_shifts: dict | None = None):
        url = f"{self.base}/schedule/{year}/{month}/lock/"
        payload = {}
        if isinstance(last_shifts, dict) and last_shifts:
            payload["last_shifts"] = last_shifts

        r = requests.post(url, json=payload)
        r.raise_for_status()
        return r.json()

    def set_admin(self, employee_id: str):
        url = f"{self.base}/admin/set/"
        r = requests.post(url, json={"employee_id": employee_id})
        r.raise_for_status()
        return r.json()

    def _force_create_month(self, payload: dict):
        url = f"{self.base}/internal/bootstrap-month/"
        r = requests.post(url, json=payload)
        r.raise_for_status()

