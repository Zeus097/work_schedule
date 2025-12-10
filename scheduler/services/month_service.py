import json
import os
from django.conf import settings
from scheduler.models import MonthRecord


class MonthService:
    """
    Central layer for:
        - extracting months from DB
        - fallback to JSON files (data/*.json)
        - writing months to DB
        - manual corrections
    """

    DATA_DIR = os.path.join(settings.BASE_DIR, "data")

    @staticmethod
    def get_latest_month():
        """
        Returns the last month from the DB.
        If not found – checks the JSON files.
        """

        record = MonthRecord.objects.order_by("-year", "-month").first()
        if record:
            return record.year, record.month, record.data

        # fallback JSON
        if not os.path.isdir(MonthService.DATA_DIR):
            return None

        json_files = [
            f for f in os.listdir(MonthService.DATA_DIR)
            if f.endswith(".json")
        ]
        if not json_files:
            return None

        json_files.sort(reverse=True)
        latest_file = json_files[0]
        path = os.path.join(MonthService.DATA_DIR, latest_file)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        year, month = latest_file.replace(".json", "").split("-")
        return int(year), int(month), data

    @staticmethod
    def get_month(year: int, month: int):
        record = MonthRecord.objects.filter(year=year, month=month).first()
        if record:
            return record.data

        # fallback JSON
        path = os.path.join(MonthService.DATA_DIR, f"{year}-{month:02d}.json")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        return None


    @staticmethod
    def save_month(year: int, month: int, data: dict):
        record, created = MonthRecord.objects.update_or_create(
            year=year,
            month=month,
            defaults={"data": data},
        )
        return record, created


    @staticmethod
    def apply_override(data, employee_name: str, day: int, value: str):
        day = str(day)

        if employee_name not in data["schedule"]:
            raise ValueError(f"Няма такъв служител: {employee_name}")

        if day not in data["schedule"][employee_name]:
            raise ValueError(f"Невалиден ден: {day}")

        data["schedule"][employee_name][day] = value
        return data


    @staticmethod
    def save_modified_month(year: int, month: int, new_data: dict):
        record, _ = MonthRecord.objects.update_or_create(
            year=year,
            month=month,
            defaults={"data": new_data},
        )
        return record


