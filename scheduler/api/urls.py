from django.urls import path, include
from scheduler.api.views import (
    ScheduleView,
    GenerateMonthView,
    EmployeeListCreateView,
    EmployeeDetailView,
    ScheduleOverrideAPI,
    LockMonthView,
    SetAdminView,
    ClearScheduleAPI,
    ClearMonthScheduleAPI,
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
    path("schedule/<int:year>/<int:month>/lock/", LockMonthView.as_view(), name="api_lock_month"),
    path("admin/set/", SetAdminView.as_view(), name="api_set_admin"),
    path("schedule/<int:year>/<int:month>/clear/", ClearScheduleAPI.as_view(),),
    path("schedule/<int:year>/<int:month>/clear/", ClearMonthScheduleAPI.as_view(),
),

]





