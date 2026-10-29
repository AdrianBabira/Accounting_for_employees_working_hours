from datetime import datetime, time, timedelta

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import EmployeeForm, ReportFilterForm, WorkEntryForm
from .models import Employee, WorkEntry


def _format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    return f"{hours} ч {remainder // 60:02} мин"


def home(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_employee":
            form = EmployeeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Сотрудник добавлен.")
                return redirect("home")
            return render(request, "tracker/home.html", _home_context(form))
        if action == "start_timer":
            employee = get_object_or_404(Employee, pk=request.POST.get("employee_id"))
            form = WorkEntryForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        WorkEntry.objects.create(
                            employee=employee, description=form.cleaned_data["description"]
                        )
                except IntegrityError:
                    messages.error(request, "У этого сотрудника уже запущен таймер.")
                else:
                    messages.success(request, "Таймер запущен.")
            else:
                messages.error(request, "Введите описание задачи.")
            return redirect("home")
        if action == "stop_timer":
            entry = get_object_or_404(
                WorkEntry, pk=request.POST.get("entry_id"), ended_at__isnull=True
            )
            entry.ended_at = timezone.now()
            entry.save(update_fields=["ended_at"])
            messages.success(request, "Таймер остановлен.")
            return redirect("home")

    return render(request, "tracker/home.html", _home_context(EmployeeForm()))


def _home_context(employee_form):
    employees = list(Employee.objects.prefetch_related("entries").all())
    for employee in employees:
        employee.active_entry = next(
            (entry for entry in employee.entries.all() if entry.is_active), None
        )

    return {
        "employee_form": employee_form,
        "employees": employees,
    }


def report(request):
    today = timezone.localdate()
    initial = {
        "date_from": today.replace(day=1),
        "date_to": today,
    }
    form = ReportFilterForm(request.GET if request.GET else initial)
    entries = []
    total_seconds = 0

    if form.is_valid():
        start = timezone.make_aware(
            datetime.combine(form.cleaned_data["date_from"], time.min)
        )
        end = timezone.make_aware(
            datetime.combine(form.cleaned_data["date_to"] + timedelta(days=1), time.min)
        )
        query = WorkEntry.objects.filter(started_at__lt=end).filter(
            Q(ended_at__isnull=True) | Q(ended_at__gt=start)
        ).select_related("employee")
        employee = form.cleaned_data["employee"]
        if employee:
            query = query.filter(employee=employee)

        now = timezone.now()
        for entry in query:
            entry.report_start = max(entry.started_at, start)
            entry.report_end = min(entry.ended_at or now, end)
            entry.report_seconds = max(
                0, int((entry.report_end - entry.report_start).total_seconds())
            )
            entry.report_duration = _format_duration(entry.report_seconds)
            entries.append(entry)
            total_seconds += entry.report_seconds

    return render(
        request,
        "tracker/report.html",
        {
            "form": form,
            "entries": entries,
            "total_seconds": total_seconds,
            "total_duration": _format_duration(total_seconds),
        },
    )
