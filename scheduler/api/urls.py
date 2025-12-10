from django.urls import path
from .views import ScheduleView, ScheduleOverrideView

urlpatterns = [
    path('schedule/<int:year>/<int:month>/', ScheduleView.as_view(), name='api_schedule'),
    path(
        'schedule/<int:year>/<int:month>/override/',
        ScheduleOverrideView.as_view(),
        name='api_schedule_override',
    ),
]
