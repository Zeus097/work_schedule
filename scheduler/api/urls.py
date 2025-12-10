from django.urls import path
from .views import (
    ScheduleView,
    ScheduleOverrideView,
    GenerateMonthView
)


urlpatterns = [
    path('schedule/<int:year>/<int:month>/', ScheduleView.as_view(), name='api_schedule'),
    path('schedule/<int:year>/<int:month>/override/', ScheduleOverrideView.as_view(), name='api_schedule_override'),

    path('schedule/generate/', GenerateMonthView.as_view(), name='api_generate_month'),
]


