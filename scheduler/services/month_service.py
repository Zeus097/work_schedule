import json
import os
from django.conf import settings
from scheduler.models import MonthRecord


class MonthService:
    """
    Централен слой за:
    - get months from the DB
    - fallback to JSON files (data/2025-12.json)
    - save into DB
    """

    DATA_DIR = os.path.join(settings.BASE_DIR, "data")

    @staticmethod
    def get_latest_month():
        """
        Returns last month from DB.
        If not – checks JSON files.
        """

        record = MonthRecord.objects.order_by("-year", "-month").first()
        if record:
            return record.year, record.month, record.data

        # Fallback -> JSON files
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


