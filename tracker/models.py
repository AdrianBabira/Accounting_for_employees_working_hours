from django.utils import timezone
from django.db import models
from django.db.models import Q


class Employee(models.Model):
    name = models.CharField("Имя сотрудника", max_length=100)
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class WorkEntry(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="entries", verbose_name="Сотрудник"
    )
    description = models.CharField("Задача", max_length=200)
    started_at = models.DateTimeField("Начало", default=timezone.now)
    ended_at = models.DateTimeField("Окончание", null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee"],
                condition=Q(ended_at__isnull=True),
                name="one_active_timer_per_employee",
            )
        ]

    @property
    def is_active(self):
        return self.ended_at is None

    def __str__(self):
        return f"{self.employee}: {self.description}"
