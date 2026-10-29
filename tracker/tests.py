from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Employee, WorkEntry


class TimeTrackingTests(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(name="Анна Иванова")

    def test_employee_can_be_added(self):
        response = self.client.post(
            reverse("home"), {"action": "add_employee", "name": "Пётр Смирнов"}
        )

        self.assertRedirects(response, reverse("home"))
        self.assertTrue(Employee.objects.filter(name="Пётр Смирнов").exists())

    def test_admin_url_loads_and_requires_login(self):
        response = self.client.get("/admin/")

        self.assertRedirects(response, "/admin/login/?next=/admin/", fetch_redirect_response=False)

    def test_timer_start_and_stop(self):
        self.client.post(
            reverse("home"),
            {
                "action": "start_timer",
                "employee_id": self.employee.pk,
                "description": "Подготовка отчёта",
            },
        )
        entry = WorkEntry.objects.get(employee=self.employee)
        self.assertIsNone(entry.ended_at)

        self.client.post(
            reverse("home"), {"action": "stop_timer", "entry_id": entry.pk}
        )
        entry.refresh_from_db()
        self.assertIsNotNone(entry.ended_at)

    def test_repeated_timer_start_does_not_create_second_active_entry(self):
        payload = {
            "action": "start_timer",
            "employee_id": self.employee.pk,
            "description": "Задача",
        }
        self.client.post(reverse("home"), payload)
        response = self.client.post(reverse("home"), payload, follow=True)

        self.assertEqual(
            WorkEntry.objects.filter(employee=self.employee, ended_at__isnull=True).count(),
            1,
        )
        self.assertContains(response, "уже запущен таймер")

    def test_empty_report_is_successful_and_explained(self):
        response = self.client.get(
            reverse("report"),
            {"date_from": "2026-03-01", "date_to": "2026-03-31"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "За выбранный период записей нет.")
        self.assertContains(response, "Всего: 0 ч 00 мин")

    def test_report_sums_time_within_selected_period(self):
        start = timezone.make_aware(datetime(2026, 3, 5, 9, 0))
        WorkEntry.objects.create(
            employee=self.employee,
            description="Работа",
            started_at=start,
            ended_at=start + timedelta(hours=2, minutes=30),
        )

        response = self.client.get(
            reverse("report"),
            {"date_from": "2026-03-01", "date_to": "2026-03-31"},
        )

        self.assertContains(response, "2 ч 30 мин")
