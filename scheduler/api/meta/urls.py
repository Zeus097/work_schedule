from django.urls import path
from .views import MetaYearsView, MetaMonthsView, MetaMonthInfoView

urlpatterns = [
    path("years/", MetaYearsView.as_view()),
    path("months/<year>/", MetaMonthsView.as_view()),
    path("month-info/<year>/<month>/", MetaMonthInfoView.as_view()),
]


