import os
import re
import calendar
from pathlib import Path

from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings

from scheduler.api.utils.holidays import get_holidays_for_month


DATA_DIR = Path(settings.BASE_DIR) / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FILE_PATTERN = re.compile(r"^(\d{4})-(\d{2})\.json$")


class MetaYearsView(APIView):
    """
    API endpoint for listing available schedule years.
    Scans stored schedule files, extracts unique years,
    and returns them in sorted order.
    """

    def get(self, request):
        years = set()

        for filename in os.listdir(DATA_DIR):
            match = FILE_PATTERN.match(filename)
            if match:
                years.add(match.group(1))

        return Response(sorted(years))


class MetaMonthsView(APIView):
    """
    API endpoint for listing available months for a given year.
    Scans stored schedule files, filters by year,
    and returns the months in chronological order.
    """

    def get(self, request, year):
        months = []

        for filename in os.listdir(DATA_DIR):
            match = FILE_PATTERN.match(filename)
            if match and match.group(1) == year:
                months.append(match.group(2))

        months.sort(key=int)
        return Response({year: months})


class MetaMonthInfoView(APIView):
    """
    API endpoint providing calendar metadata for a given month.
    Returns total days, weekend dates, and official holidays.
    """

    def get(self, request, year, month):
        year = int(year)
        month = int(month)

        days = calendar.monthrange(year, month)[1]

        weekends = [
            d for d in range(1, days + 1)
            if calendar.weekday(year, month, d) in (5, 6)
        ]

        holidays = get_holidays_for_month(year, month)

        return Response({
            "year": year,
            "month": month,
            "days": days,
            "weekends": weekends,
            "holidays": holidays
        })
