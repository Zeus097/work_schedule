from django.db import models
import calendar


class Employee(models.Model):
    full_name = models.CharField(max_length=255, unique=True)
    card_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class MonthAdmin(models.Model):
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="month_admins"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("year", "month")
        ordering = ["-year", "-month"]

    def __str__(self) -> str:
        return f"{self.employee.full_name} – {self.year}-{self.month:02d}"


class MonthRecord(models.Model):
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("year", "month")
        ordering = ["-year", "-month"]

    def __str__(self) -> str:
        return f"{self.year}-{self.month:02d}"

    @property
    def label(self) -> str:
        return f"{calendar.month_name[self.month]} {self.year}"
