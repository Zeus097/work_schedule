from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from scheduler.models import MonthRecord
from scheduler.logic.generator.generator import generate_new_month

from scheduler.api.errors import api_error

from scheduler.api.serializers import (
    DayRecordSerializer,
    OverrideSerializer,
    GenerateMonthSerializer
)


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






class ScheduleView(APIView):
    def get(self, request, year, month):
        # Checking if the month exists
        records = MonthRecord.objects.filter(year=year, month=month)

        # If not – generate a new one
        if not records.exists():
            generate_new_month(year, month)
            records = MonthRecord.objects.filter(year=year, month=month)

        # serialization
        serializer = DayRecordSerializer(records, many=True)
        return Response({
            "year": year,
            "month": month,
            "days": serializer.data
        }, status=status.HTTP_200_OK)


class ScheduleOverrideView(APIView):
    def post(self, request, year, month):

        # 1) validate the input
        input_serializer = OverrideSerializer(data=request.data)
        if not input_serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Подадените данни са невалидни.",
                hint=str(input_serializer.errors)
            )

        data = input_serializer.validated_data

        employee_id = data['employee_id']
        day = data['day']
        new_shift = data['new_shift']

        # 2) we ensure that the month exists
        if not MonthRecord.objects.filter(year=year, month=month).exists():
            generate_new_month(year, month)

        # 3) we find the specific record
        try:
            record = MonthRecord.objects.get(
                year=year,
                month=month,
                day=day,
                employee_id=employee_id,
            )
        except MonthRecord.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Няма запис за избрания служител в този ден.",
                hint="Проверете дали служителят и денят са валидни.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        # 4) apply override
        record.shift = new_shift
        record.is_override = True
        record.save()

        # 5) we bring back the renewed day
        output_serializer = DayRecordSerializer(record)
        return Response(output_serializer.data, status=status.HTTP_200_OK)





class GenerateMonthView(APIView):
    def post(self, request):
        serializer = GenerateMonthSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни параметри за генериране на месец.",
                hint=str(serializer.errors)
            )

        data = serializer.validated_data
        year = data['year']
        month = data['month']


        generate_new_month(year, month)


        records = MonthRecord.objects.filter(year=year, month=month)
        out = DayRecordSerializer(records, many=True)

        return Response({
            "year": year,
            "month": month,
            "generated": True,
            "days": out.data
        }, status=status.HTTP_201_CREATED)


