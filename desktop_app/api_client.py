import requests
from config import API_BASE_URL


class APIClient:
    def __init__(self):
        self.base = API_BASE_URL

    # -------------------------
    #   META
    # -------------------------
    def get_years(self):
        r = requests.get(f"{self.base}/meta/years/")
        r.raise_for_status()
        return r.json()

    def get_month_info(self, year: int, month: int):
        r = requests.get(f"{self.base}/meta/month-info/{year}/{month}/")
        r.raise_for_status()
        return r.json()

    # -------------------------
    #   SCHEDULE
    # -------------------------
    def get_schedule(self, year: int, month: int):
        r = requests.get(f"{self.base}/schedule/{year}/{month}/")
        if r.status_code == 404:
            raise FileNotFoundError
        r.raise_for_status()

        data = r.json()

        # 🔧 FIX 1 — normalize schedule (day keys -> int)
        raw_schedule = data.get("schedule", {})
        normalized_schedule = {
            emp: {int(day): shift for day, shift in days.items()}
            for emp, days in raw_schedule.items()
        }

        data["schedule"] = normalized_schedule
        return data

    def generate_month(self, year: int, month: int):
        r = requests.post(
            f"{self.base}/schedule/generate/",
            json={"year": year, "month": month}
        )
        r.raise_for_status()
        return r.json()

    # -------------------------
    #   OVERRIDE
    # -------------------------
    def post_override(self, year, month, data):
        url = f"{self.base}/schedule/{year}/{month}/override/"
        r = requests.post(url, json=data)
        r.raise_for_status()
        return r.json()

    # -------------------------
    #   EMPLOYEES
    # -------------------------
    def get_employees(self):
        r = requests.get(f"{self.base}/employees/")
        r.raise_for_status()
        return r.json()

    def add_employee(self, data):
        r = requests.post(f"{self.base}/employees/", json=data)
        r.raise_for_status()
        return r.json()

    def update_employee(self, emp_id, data):
        r = requests.put(f"{self.base}/employees/{emp_id}/", json=data)
        r.raise_for_status()
        return r.json()

    def delete_employee(self, emp_id):
        r = requests.delete(f"{self.base}/employees/{emp_id}/")
        r.raise_for_status()
        return True




