from rest_framework import serializers
from scheduler.models import Employee


class GenerateMonthSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField(min_value=1, max_value=12)


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'full_name', 'is_active', 'start_date', 'end_date']


class EmployeeUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, max_length=255)
    is_active = serializers.BooleanField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)



class OverrideSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    day = serializers.IntegerField(min_value=1, max_value=31)
    new_shift = serializers.CharField(max_length=5)
