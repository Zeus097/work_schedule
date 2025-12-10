from django.db import models
import calendar


class Employee(models.Model):
    full_name = models.CharField(max_length=255, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)   # <-- ново
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name



class AdminEmployee(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="admin_profile",
    )
    is_super_admin = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Admin: {self.employee.full_name}"


class MonthRecord(models.Model):
    """
    Holds the whole json for the month generator.
    Example:
      {
        "schedule": {...},
        "meta": {...},
        ...
      }
    """

    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()  # 1–12
    data = models.JSONField()  # result from generate_new_month(...)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("year", "month")
        ordering = ["-year", "-month"]

    def __str__(self) -> str:
        return f"{self.year}-{self.month:02d}"

    @property
    def label(self) -> str:
        """Text for UI/admin."""

        month_name = calendar.month_name[self.month]
        return f"{month_name} {self.year}"



