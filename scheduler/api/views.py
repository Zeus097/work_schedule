from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from scheduler.models import MonthRecord, Employee
from scheduler.logic.generator.generator import generate_new_month

from scheduler.api.errors import api_error

from scheduler.api.serializers import (
    OverrideSerializer,
    GenerateMonthSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer
)



class ScheduleView(APIView):
    def get(self, request, year, month):

        # check if month exists
        try:
            record = MonthRecord.objects.get(year=year, month=month)
        except MonthRecord.DoesNotExist:
            generate_new_month(year, month)
            record = MonthRecord.objects.get(year=year, month=month)

        # return raw JSON data
        return Response({
            "year": year,
            "month": month,
            "data": record.data
        }, status=status.HTTP_200_OK)






class ScheduleOverrideView(APIView):
    def post(self, request, year, month):
        return api_error(
            code="NOT_SUPPORTED",
            message="Override функционалността ще бъде активирана след обновяване на JSON структурата.",
            hint="Очаква се във Фаза 2 – Стъпка 6.",
            http_status=status.HTTP_400_BAD_REQUEST
        )





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

        # Generate month (returns dict)
        generated = generate_new_month(year, month)

        # Return the raw JSON
        return Response({
            "year": year,
            "month": month,
            "generated": True,
            "data": generated
        }, status=status.HTTP_201_CREATED)







class EmployeeListCreateView(APIView):
    def get(self, request):
        employees = Employee.objects.all().order_by('full_name')
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)

        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни данни за създаване на служител.",
                hint=str(serializer.errors)
            )

        employee = serializer.save()
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)



class EmployeeDetailView(APIView):
    def put(self, request, id):
        # lookup
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Служителят не е намерен.",
                hint="Проверете дали ID-то е валидно.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        # validation
        serializer = EmployeeUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="INVALID_INPUT",
                message="Невалидни данни за редакция.",
                hint=str(serializer.errors)
            )

        data = serializer.validated_data

        # update only the provided fields
        for field, value in data.items():
            setattr(employee, field, value)

        employee.save()

        return Response(EmployeeSerializer(employee).data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        # lookup
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Служителят не е намерен.",
                hint="Проверете ID-то.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        employee.delete()

        return Response({"status": "deleted"}, status=status.HTTP_204_NO_CONTENT)



