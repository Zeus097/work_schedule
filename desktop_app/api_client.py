import requests
from config import API_BASE_URL

class APIClient:
    def __init__(self):
        self.base = API_BASE_URL

    def get_years(self):
        return requests.get(f"{self.base}/meta/years/").json()

    def get_months(self, year: int):
        return requests.get(f"{self.base}/meta/months/{year}/").json()

    def get_month_info(self, year: int, month: int):
        return requests.get(f"{self.base}/meta/month-info/{year}/{month}/").json()
