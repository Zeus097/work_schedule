from django.contrib import admin
from .models import Employee, AdminEmployee, MonthRecord


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "is_active", "start_date", "created_at")
    list_filter = ("is_active",)
    search_fields = ("full_name",)


@admin.register(AdminEmployee)
class AdminEmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee", "is_super_admin", "created_at")


@admin.register(MonthRecord)
class MonthRecordAdmin(admin.ModelAdmin):
    list_display = ("year", "month", "label", "created_at")
    list_filter = ("year", "month")
    search_fields = ("year", "month")


