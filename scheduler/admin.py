from django.contrib import admin
from .models import Employee, MonthAdmin, MonthRecord


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "card_number",
        "is_active",
        "start_date",
        "end_date",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("full_name",)
    ordering = ("full_name",)


@admin.register(MonthAdmin)
class MonthAdminAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "year",
        "month",
        "created_at",
    )
    list_filter = ("year", "month")
    search_fields = ("employee__full_name",)
    ordering = ("-year", "-month")


@admin.register(MonthRecord)
class MonthRecordAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "month",
        "label",
        "created_at",
        "updated_at",
    )
    list_filter = ("year", "month")
    ordering = ("-year", "-month")
