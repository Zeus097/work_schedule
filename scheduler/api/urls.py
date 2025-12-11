from django.urls import path, include
from scheduler.api.views import (
    ScheduleView,
    GenerateMonthView,
    EmployeeListCreateView,
    EmployeeDetailView,
    ScheduleOverrideAPI,
)

urlpatterns = [
    # --- Schedule API ---
    path('schedule/<int:year>/<int:month>/', ScheduleView.as_view(), name='api_schedule'),
    path('schedule/generate/', GenerateMonthView.as_view(), name='api_generate_month'),
    path(
        'schedule/<int:year>/<int:month>/override/',
        ScheduleOverrideAPI.as_view(),
        name='api_schedule_override'
    ),

    # --- Employees API ---
    path('employees/', EmployeeListCreateView.as_view(), name='api_employees'),
    path('employees/<int:id>/', EmployeeDetailView.as_view(), name='api_employee_detail'),

    # --- META API (новото) ---
    path("meta/", include("scheduler.api.meta.urls")),
]
