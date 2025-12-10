from rest_framework import serializers
from scheduler.models import MonthRecord

class DayRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthRecord
        fields = ['day', 'shift', 'employee_name', 'is_override']





class DayRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthRecord
        fields = ['day', 'shift', 'employee_name', 'is_override']


class OverrideSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    day = serializers.IntegerField(min_value=1, max_value=31)
    new_shift = serializers.CharField(max_length=5)   # 'Д', 'Н', 'В', 'П' и e.t.c.


class GenerateMonthSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField(min_value=1, max_value=12)
