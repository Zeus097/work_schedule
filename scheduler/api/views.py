from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from scheduler.models import MonthRecord
from scheduler.logic.generator.generator import generate_new_month

from .serializers import DayRecordSerializer


class ScheduleView(APIView):
    def get(self, request, year, month):

        # Checking if the month exists
        records = MonthRecord.objects.filter(year=year, month=month)

        # If not – generate a new one
        if not records.exists():
            generated = generate_new_month(year, month)

            # the generated returns dict
            records = MonthRecord.objects.filter(year=year, month=month)

        # serialization
        serializer = DayRecordSerializer(records, many=True)
        return Response({
            "year": year,
            "month": month,
            "days": serializer.data
        }, status=status.HTTP_200_OK)


