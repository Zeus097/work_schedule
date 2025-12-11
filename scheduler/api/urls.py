from django.urls import path
from scheduler.api.views import (
    ScheduleView,
    ScheduleOverrideView,
    GenerateMonthView,
    EmployeeListCreateView,
    EmployeeDetailView,
    ScheduleOverrideAPI,
)

urlpatterns = [
    path('schedule/<int:year>/<int:month>/', ScheduleView.as_view(), name='api_schedule'),
    path('schedule/<int:year>/<int:month>/override/', ScheduleOverrideView.as_view(), name='api_schedule_override'),

    path('schedule/generate/', GenerateMonthView.as_view(), name='api_generate_month'),

    path('employees/', EmployeeListCreateView.as_view(), name='api_employees'),
    path('employees/<int:id>/', EmployeeDetailView.as_view(), name='api_employee_detail'),
    path(
        "schedule/<int:year>/<int:month>/override/",
        ScheduleOverrideAPI.as_view(),
    ),
]


