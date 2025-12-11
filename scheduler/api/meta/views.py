import os
import calendar
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings


DATA_DIR = settings.BASE_DIR / "data"


class MetaYearsView(APIView):
    def get(self, request):
        years = []

        for item in os.listdir(DATA_DIR):
            if item.isdigit() and os.path.isdir(DATA_DIR / item):
                years.append(item)

        years.sort()
        return Response(years)


class MetaMonthsView(APIView):
    def get(self, request, year):
        year_dir = DATA_DIR / year
        if not year_dir.exists():
            return Response({year: []})

        months = []

        for file in os.listdir(year_dir):
            if file.endswith(".json"):
                month = file.replace(".json", "")
                if month.isdigit():
                    months.append(month)

        months.sort(key=lambda x: int(x))
        return Response({year: months})


class MetaMonthInfoView(APIView):
    def get(self, request, year, month):
        year = int(year)
        month = int(month)

        days = calendar.monthrange(year, month)[1]
        weekday_start = calendar.monthrange(year, month)[0]  # Monday=0

        weekday_map = {}
        for d in range(1, days + 1):
            weekday_map[str(d)] = calendar.weekday(year, month, d)

        return Response({
            "days": days,
            "weekday_start": weekday_start,
            "weekday_map": weekday_map
        })



