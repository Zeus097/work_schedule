from django.urls import path
from .views import (
    MetaYearsView,
    MetaMonthsView,
    MetaMonthInfoView
)

urlpatterns = [
    path("years/", MetaYearsView.as_view(), name="meta_years"),
    path("months/<year>/", MetaMonthsView.as_view(), name="meta_months"),
    path("month-info/<year>/<month>/", MetaMonthInfoView.as_view(), name="meta_month_info"),
]
