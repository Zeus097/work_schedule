from rest_framework import serializers
from scheduler.models import MonthRecord

class DayRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthRecord
        fields = ['day', 'shift', 'employee_name', 'is_override']
