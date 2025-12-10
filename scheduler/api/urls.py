from django.urls import path
from .views import ScheduleView

urlpatterns = [
    path('schedule/<int:year>/<int:month>/', ScheduleView.as_view(), name='api_schedule'),
]
